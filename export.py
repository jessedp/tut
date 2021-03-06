import gevent
import os
import contextlib
import shutil
import socket
import tempfile
import logging

from tqdm import tqdm
import ffmpeg


from tinydb import TinyDB, Query

from config import built_ins
from recording import Recording

logger = logging.getLogger(__name__)


def copy(id_list, args):
    total = len(id_list)
    if total == 0:
        print(f"Nothing to process, exiting...")
        return
    elif total == 1:
        print(f"Processing {total} recording")
    else:
        print(f"Processing {total} recordings")
    print("-"*50)
    for id in id_list:
        # TODO: put a X of Y somewhere near here
        _copy(id, args)
        print()
    print("FINISHED")


def _copy(obj_id, args):
    # TODO: Whoops, now used this twice (search.py too)
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    shows = Query()
    # shortcut for later
    shows_qry = shows.data
    # TODO: deal with pieces of the same recording (TMSID?) marked "finished"
    #      ie, 2 portions (non-full) of the an episode
    #        + just skip them (do this!)
    #        + differentiate on recorded at the same time
    #           - look at recording/show data to see what it *should* be?
    #        - overwrite previous portions
    obj = rec_db.get(
        (shows_qry.object_id == int(obj_id))
        &
        (shows_qry.video_details.state == 'finished')
    )
    if obj is None:
        print(
            f'ERROR: Unable to find recording with object_id == "{obj_id}", '
            f'skipping...')
        return

    rec = Recording(obj['data'])

    watch = rec.watch()
    if watch.error is not None:
        print(rec.get_description())
        print("ERROR: Recording no longer exists, skipping!")
        return
    out_file = rec.get_out_path('mp4')
    # TODO: this could make weird dirs?
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    # Display what we're working on
    if built_ins['log_level'] <= logging.INFO:
        rec.print()
        watch.dump_info()
    else:
        print(rec.get_description())
        print(" " * 2 + f"writing to: {out_file}")

    if not args.clobber and os.path.exists(out_file):
        print("File exists, skipping")
        return

    total_duration = float(ffmpeg.probe(
        watch.playlist_url)['format']['duration'])

    if built_ins['dry_run']:
        # maybe do a dry run writing to a temp path and deleting so the time
        # is roughly the same?
        print("DRY RUN: The recording wasn't saved.")
    else:
        with show_progress(total_duration) as socket_filename:
            try:
                copier = (
                    ffmpeg
                    # this is a m3u8 playlist
                    .input(watch.playlist_url)
                    .output(out_file, codec='copy',
                            preset='ultrafast', loglevel='info')
                    .overwrite_output()
                    .global_args(
                        '-progress', 'unix://{}'.format(socket_filename)
                    )
                )

                copier.run(capture_stdout=True, capture_stderr=True)
            except KeyboardInterrupt:
                os.remove(out_file)
                raise KeyboardInterrupt
            except ffmpeg.Error as e:
                logger.error(e)


# TODO: all of this should probably be somewhere else...
@contextlib.contextmanager
def _tmpdir_scope():
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def _do_watch_progress(filename, sock, handler):
    """Function to run in a separate gevent greenlet to read progress
    events from a unix-domain socket."""
    connection, client_address = sock.accept()
    data = b''
    try:
        while True:
            more_data = connection.recv(16)
            if not more_data:
                break
            data += more_data
            lines = data.split(b'\n')
            for line in lines[:-1]:
                line = line.decode()
                parts = line.split('=')
                key = parts[0] if len(parts) > 0 else None
                value = parts[1] if len(parts) > 1 else None
                handler(key, value)
            data = lines[-1]
    finally:
        connection.close()


@contextlib.contextmanager
def _watch_progress(handler):
    """Context manager for creating a unix-domain socket and listen for
    ffmpeg progress events.
    The socket filename is yielded from the context manager and the
    socket is closed when the context manager is exited.
    Args:
        handler: a function to be called when progress events are
            received; receives a ``key`` argument and ``value``
            argument. (The example ``show_progress`` below uses tqdm)
    Yields:
        socket_filename: the name of the socket file.
    """
    with _tmpdir_scope() as tmpdir:
        socket_filename = os.path.join(tmpdir, 'sock')
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        with contextlib.closing(sock):
            sock.bind(socket_filename)
            sock.listen(1)
            child = gevent.spawn(_do_watch_progress,
                                 socket_filename, sock, handler)
            try:
                yield socket_filename
            except Exception:
                gevent.kill(child)
                raise


@contextlib.contextmanager
def show_progress(total_duration):
    """Create a unix-domain socket to watch progress and render tqdm
    progress bar."""
    with tqdm(total=round(total_duration, 2)) as bar:
        def handler(key, value):
            if key == 'out_time_ms':
                time = round(float(value) / 1000000., 2)
                bar.update(time - bar.n)
            elif key == 'progress' and value == 'end':
                bar.update(bar.total - bar.n)

        with _watch_progress(handler) as socket_filename:
            yield socket_filename
