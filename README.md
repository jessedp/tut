<a name="tut"></a>
**Tut** lets you mess with your 
[Tablo](https://www.tablotv.com/). Some things it does:

* automatically finds your Tablo (there are options if you have multiples)
* builds a library of your recordings
* display some stats about the library
* a large number of search options

Matching searches can than be used to:
* **delete** recordings from your Tablo
* **copy** recordings to wherever   

Here's a fun example that _could_ be used to cleanup crappy recordings
on your Tablo:
```shell script
./tut.py -L search --duration 30s | ./tut.py delete
```  


###### Requirements
It is written for python 3 and tested against Python 3.7.3 on Ubuntu.

Tested against Tablo firmware:
* v.2.2.26   


### Installation
Download and unpack the 
[zip of this project](https://github.com/jessedp/tut/archive/master.zip) 
or clone it. Go there and...
* run `pip install -r requirements.xt`

_You maybe want to run this in a [virtualenv](https://virtualenv.pypa.io/en/latest/)_


### Kick the wheels
With any luck after you've installed it, you can run these commands
and it'll do/display a bunch of stuff about your Tablo. See below for 
details on all sorts of other stuff you can do.
```
./tut.py config --discover
./tut.py library --build
./tut.py library --stats
./tut.py search --limit 2
```

### Detailed Usage
Run something like:

* `./tut.py`
* `python tut.py`
* `python3 tut.py`
 
and you should see something like:

```
usage: tut.py [-h] [--dry-run] [-L] [-v] [--version]
              {config,library,search,copy,delete} ...

Available commands:
  {config,library,search,copy,delete}
    config              manage configuration options
    library             manage the local library of recordings
    search              ways to search your library
    copy                copy recordings somewhere
    delete              delete recordings from the Tablo device

optional arguments:
  -h, --help            show this help message and exit
  --dry-run             show what would happen, but don't change anything
  -L, --id-list         if possible, only output a list of matching Object Ids
                        - Pipe this into other commands. (overrides --full and
                        any other output)
  -v, --verbose         amount of detail to display add vs (-vvvv) for maximum
                        amount
  --version             show program's version number and exit
```

### Configure
First things first, get your Tablo set up: 

`./tut.py config --discover`

Want to see some gory details of what happened there?

`./tut.py -vvv config --discover`  (more v, more info)

Then try:

`./tut.py config --view`

Possibly you want to look at the config file it told you exists?

### Build Your Library
Before you can do anything useful, you'll need to build the local cache/library of your recordings:

`./tut.py library --build`

A slow run on 630 recordings takes about 40 sec. 


You can view some basic stats about your library using:

`./tut.py library --stats`

And you'll see something like:
```
Overview
--------------------------------------------------
Total Recordings: 609
Total Watched: 65

By Current Recording State
--------------------------------------------------
Finished         : 577
Failed           : 32
Recording        : 0

By Recording Type
--------------------------------------------------
Episodes/Series  : 608
Movies           : 1
Sports/Events    : 0
Programs         : 0
```

### Search the Library
There are a number of ways to search your library. This will be useful in specifying recordings you want to work with later.

Run `./tut.py search` to see the numerous options available.

**Important** - use the **-L** flag on _any_ search to create a list that can be 
piped into other opertaions.

A few examples follow. Note the combination of flags. 

###### All recordings with "colbert" in the title or description:

`./tut.py search colbert`   

or:

`./tut.py search --term colbert`

###### Or limit that to only recordings after a specific date:

`./tut.py search colbert --after 2019-07-19`

###### View all Failed recordings:

`./tut.py search --state failed`

###### Return at most 3 Failed recordings:

`./tut.py search --state failed --limit 3`

###### Return all the Movies:

`./tut.py search --type movie`

###### Return all the Movies, but dump the full data record:

`./tut.py search --type movie --full`

###### Find all recordings 30 seconds or shorter
`./tut.py -L search --duration 30s`


### Delete
Do a search, add the **-L** flag and pipe it into delete:

`./tut.py -L search --duration 30s | ./tut.py delete `

_Note_: you'll have to add a `--yes` flag to make the delete actually occur.


 
 #### Acknowledgement
 This wouldn't have been made without: 
 * [the code for the Kodi add-on](https://github.com/Nuvyyo/script.tablo) from the Nuvyyo folks. You'll find the slightly modified version of it  `tablo` module.
 
 * [TinyDB](https://github.com/msiemens/tinydb)
 