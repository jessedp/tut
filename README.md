## Tut - Tablo User Tools
**Tut** lets you mess with your 
[Tablo](https://www.tablotv.com/). Mostly just retrieving  
recordings and their associated data. It aims to be easily usable with no configuration out-of-the-box. One 
would likely, of course, do additional configuration later.

It is written for python 3.  


### Installation
Download and unpack the 
[zip of this project](https://github.com/jessedp/tut/archive/master.zip) 
or clone it. Go there and..
* run `pip install -r requirements.xt`

### Usage
Basics, run something like:

* `./tut.py`
* `python tut.py`
* `python3 tut.py`
 
and you should see something like:

```
usage: tut.py [-h] [-v] [--dry-run] [--version] {config,library} ...

Available commands:
  {config,library}  available commands
    config          manage configuration options
    library         manage the local library of Tablo recordings

optional arguments:
  -h, --help        show this help message and exit
  -v, --verbose     amount of program detail to output
  --dry-run         show what would happen, but don't change anything
  --version         show program's version number and exit
```

First things first, get your Tablo setup: 

`./tut.py config --discover`

Want to see some gory details of what happened there?

`./tut.py -vvv config --discover`  (more v, more info)

Then try:

`./tut.py config --view`

Possibly you want to look at the config file it told you exists now?

Next, maybe:

`/tut.py library --build` or `/tut.py -vvv library --build`

And you can search (titles currently) using

`/tut.py library --search Colbert`   
 
 
 #### Acknowledgement
 This wouldn't have been made without 
 [the code](https://github.com/Nuvyyo/script.tablo) of the Nuvyyo folk. 