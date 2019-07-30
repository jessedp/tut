## Tut - Tablo User Tools
**Tut** lets you mess with your 
[Tablo](https://www.tablotv.com/). Mostly just retrieving recordings and their associated data. It aims to be easily usable with no configuration 
out-of-the-box. One would likely, of course, do additional configuration later.

It is written for python 3.

Tested against Tablo firmware:
* v.2.2.26
   


### Installation
Download and unpack the 
[zip of this project](https://github.com/jessedp/tut/archive/master.zip) 
or clone it. Go there and...
* run `pip install -r requirements.xt`

_You maybe want to run this in a [virtualenv](https://virtualenv.pypa.io/en/latest/)_

### Usage
Basics, run something like:

* `./tut.py`
* `python tut.py`
* `python3 tut.py`
 
and you should see something like:

```
usage: tut.py [-h] [-v] [--dry-run] [--version] {config,library,search} ...

Available commands:
  {config,library,search}
                        available commands
    config              manage configuration options
    library             manage the local library of Tablo recordings
    search              library search options

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         amount of program detail to output
  --dry-run             show what would happen, but don't change anything
  --version             show program's version number and exit
```

### Configure
First things first, get your Tablo set up: 

`./tut.py config --discover`

Want to see some gory details of what happened there?

`./tut.py -vvv config --discover`  (more v, more info)

Then try:

`./tut.py config --view`

Possibly you want to look at the config file it told you exists now?

### Library
Before you can do anything useful, you'll need to build the local cache/library of your recordings:

`/tut.py library --build` or `/tut.py -vvv library --build`

You can view some basic stats about your library using

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

### Search
There are a number of ways to search your library. This will be useful in specifying recordings you want to work with later.

Run `./tut.py search` to see the numerous options available.

A few examples: 

All recordings with "colbert" the title or description:

`./tut.py search colbert`   

or:

`./tut.py search --term colbert`

Or limit that to only recordings after a specific date:

`./tut.py search colbert --after 2019-07-19`

View all Failed recordings:

`./tut.py search --state failed`

Return at most 3  Failed recordings:

`./tut.py search --state failed --limit 3`

Return all the Movies:

`./tut.py search --type movie`

Return all the Movies, but dump the full data record:

`./tut.py search --type movie --full`

 
 #### Acknowledgement
 This wouldn't have been made without: 
 * [the code for the Kodi add-on](https://github.com/Nuvyyo/script.tablo) from the Nuvyyo folks. You'll find the slightly modified version of it  `tablo` module.
 
 * [TinyDB](https://github.com/msiemens/tinydb)
 