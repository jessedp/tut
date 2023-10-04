from datetime import timedelta
from tablo.entities.airing import Airing
from util import convert_datestr
from config import config


class Recording(Airing):
    def __init__(self, data):
        super(Recording, self).__init__(data)

    def print(self):
        # TODO: shorten desc
        # TODO: format statuses better
        sep = '\t'
        error = None
        if self.video_details['error']:
            error = self.video_details['error']['code'] \
                + ' - ' + self.video_details['error']['details']

        if self.type == 'episode':
            # TODO: type as an indicator (M) == movie (S) == series/episode ?
            # TODO: (earlier) levels of display (normally -vvv)

            print(
                f"{self.get_description()}\n"
                f"{sep}{self.episode['description']}\n"
                f"{sep}Season: {self.get_epsiode_num()}"
                f"  Status: {self.video_details['state']}"
                f"  Watched: {self.user_info['watched']}\n"
                f"{sep}Length: {self.get_dur()}\n"
                f"{sep}Type: {self.type}"
                f"  TMS ID: {self.episode['tms_id']}"
                f"  Rec Object ID: {self.object_id}"
            )
            if error:
                print(f"{sep}ERROR: {error}")

        elif self.type == 'movie':
            print(
                convert_datestr(self.airing_details['datetime']) + " - " +
                f"{self.airing_details['show_title']}\n"
                f"  Type: {self.type}"
            )
        else:
            self.dump_info()

        print(f'{sep}output file name:')
        print(sep*2 + self.get_out_path())
        print()

    def get_description(self):
        output = convert_datestr(self.airing_details['datetime']) + " - " \
            + f"{self.object_id} - " \
            + f"{self.airing_details['show_title']}" \
            + f" - {self.get_title()}"
        return output

    def get_title(self, for_print=True):
        if not self.type == 'episode':
            return ""
        if for_print:
            title = self.episode['title']
            if not title or title == 'None':
                # This gem brought to you by Buzzr, Celebrity Name Game, and/or
                # maybe TMSIDs that start with "SH"
                if self.episode['season_number'] == 0 \
                        and self.episode['number'] == 0:
                    return self.airing_details['datetime']\
                        .replace("-", "").replace(":", "")\
                        .replace("T", "_").replace("Z", "")
                else:
                    return self.get_epsiode_num()
            # yuck - "105" = season 1 + episode 5
            if title == str(self.episode['season_number']) + \
                    '{:02}'.format(self.episode['number']):
                return self.get_epsiode_num()
            return title
        return "WTF?"

    def get_epsiode_num(self):
        return "s{:02}".format(self.episode['season_number']) + \
            'e{:02}'.format(self.episode['number'])

    def get_out_path(self, ext="EXT"):
        if self.type == 'episode':
            title = self.airing_details['show_title']
            out = config.get('Output Locations', 'TV') + '/'
            out += title + '/'
            out += 'Season {:02}'.format(self.episode['season_number']) + '/'
            out += title + \
                ' - s{:02}'.format(self.episode['season_number']) + \
                'e{:02}'.format(self.episode['number'])
            return out + "." + ext
        elif self.type == 'movie':
            out = config.get('Output Locations', 'Movies') + '/'
            out += f"{self.airing_details['show_title']}"
            out += f" - {self.movie_airing['release_year']}"
            return out+"." + ext
        else:
            return f"{self.type } is UNDEFINED"

    def get_dur(self):
        return self.get_actual_dur() + " of " + self.get_proper_dur()

    def get_proper_dur(self):
        return str(timedelta(seconds=self.airing_details['duration']))

    def get_actual_dur(self):
        return str(timedelta(seconds=self.video_details['duration']))
