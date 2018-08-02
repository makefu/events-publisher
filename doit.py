#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.requests -p python3Packages.twitter -p python3Packages.docopt -p python3Packages.dateutil -p python3Packages.pytz
""" usage: doit.py [options]

Options:
    --init              performs an initial run which will not publish all new events
    --clean             removes the database at startup
    --mock              mock the requests and use events.json and series.json locally
    --lol=LEVEL         set log level [Default: INFO]
    --days=D            Offset in days when to announce an event (starting 0:00) [Default: 0]
    --hours=H           Offset in hours [Default: 11]
    --minutes=M         Offset in minutes [Default: 30]

By default we announce a new event at 12:30 the day before
"""


from os import remove
import requests
import shelve
import logging
log = logging.getLogger('cli')
def set_lol(lol):
  numeric_level = getattr(logging,lol.upper(),None)
  if not isinstance(numeric_level,int):
    raise AttributeError('No such log level {}'.format(lol))
  logging.basicConfig(level=numeric_level)
  log.setLevel(numeric_level)

statefile = 'state.db'

# event: { ...
#   announce: {
#     new: False
#     next_day: False
#   }
# }


# from dateutil.relativedelta import *
from dateutil.rrule import *
from dateutil.parser import *
from datetime import *
import pytz

now = datetime.now(pytz.utc)

def within_offset(event,offset):
    event_start = parse(event['start']).replace(hour=0,minute=0,second=0,microsecond=0)
    log.debug(f"{event['name']}: {event_start-offset} < {now} < {event_start}")
    isTomorrow = event_start-offset < now < event_start
    if isTomorrow:
        log.info(f"event {event['name']} starts in the next {offset} days - exactly {event_start-now} from now")
        log.debug(f"{event['name']}: {event_start-offset} < {now} < {event_start}")
        return isTomorrow

def inthepast(event):
    event_end = parse(event['end'])
    log.debug(f"{event['name']}: {event_end} < {now} ")
    return event_end < now
def running(event):
    return parse(event['start']) < now < parse(event['end'])

def days_till(event):
    return (parse(event['start']).date() - now.date()).days

def announce(text):
    log.info(f"Announcing {text}")
    try:
        announce_mastodon(text)
    except Exception as e:
        log.error("Unable to announce to mastodon")
        log.info(f"Error Reason: {e}")

def announce_mastodon(text):
    visibility='unlisted'
    from mastodon import Mastodon
    mastodon = Mastodon(
        api_base_url = 'https://chaos.social',
        access_token = 'shack-publisher_usercred.secret'
    )
    mastodon.status_post(text,visibility='private')


def update(offset,init=False,mock=False):
    # filter all events with no ID as they are part of a series
    if mock:
        import json
        new_events = list(filter(lambda f: f['id'], json.load(open('events.json'))))
        new_series = json.load(open('series.json'))
    else:
        new_events = list(filter(lambda f: f['id'], requests.get('https://events-api.shackspace.de/events/').json()))
        new_series = requests.get('https://events-api.shackspace.de/series/').json()

    state = shelve.open(statefile)
    if not 'events' in state:
        log.info("Creating new state events")
        state['events'] = new_events
        state['series'] = new_series

    events = state['events']
    series = state['series']
    if init:
        log.info("Will not publish the new events")
        for event in events:
            if not 'announce' in event: event['announce'] = {  }
            event['announce']['new'] = True
            if within_offset(event,offset):
                log.debug(f"event {event['name']} is within offset, setting announce to true")
                event['announce']['tomorrow'] = True
        for event in series:
            if not 'announce' in event: event['announce'] = {  }
            # find next event date logic
            next_event = rrulestr(event['rrule'],
                                  dtstart=datetime.now(pytz.utc)).between(datetime.now(pytz.utc),datetime.now(pytz.utc)+timedelta(days=365))[0]
            event_start = datetime.strptime(event['start'],"%H:%M:%S")
            next_event = next_event.replace(hour=event_start.hour,minute=event_start.minute,second=event_start.second)
            # start is actually the time when the event begins
            # we want to recycle nextday, which uses event['start'] so we override
            event['time'] = event['start']
            event['start'] = next_event.isoformat()
            event['announce']['new'] = True
            if within_offset(event,offset):
                log.info(f"series {event['name']} is within offset, setting announce to true")
                event['announce']['tomorrow'] = True
    else:
        for event in events:
            url = f"https://events.shackspace.de/events/{event['id']}"
            ts = datetime.strftime(parse(event['start']),"%A, dem %d. %B, %-H:%M Uhr")
            days = days_till(event)
            if inthepast(event):
                log.debug(f"Skipping {event['name']} because start date is in the past")
                continue
            if not 'announce' in event: event['announce'] = {  }

            if not 'new' in event['announce'] or event['announce']['new'] == False:
                log.info(f"{event['name']} has not been announced yet and is new")
                event['announce']['new'] = True
                announce(f"Neues Event im shack!\n{event['name']} am {ts} - {url}")
            elif not 'tomorrow' in event['announce'] or event['announce']['tomorrow'] == False:
                if within_offset(event,offset):
                    log.info(f"event {event['name']} is within offset and has not been announced yet")
                    event['announce']['tomorrow'] = True
                    announce(f"Erinnerung:\nIn {days} Tagen, am {ts} findet im shack '{event['name']}' statt - {url}")
                else:
                    event['announce']['tomorrow'] = False


        # for all series:
            # if a new date has been calculated, reset the annouce flag
            # if series has been announced: ignore
            # if series has not been announced and is new: annouce as "new series on ... at ... + link`
            # if series is in the next day and has not been announced: announce as `tomorrow at ... starts`
        pass


    state['events'] = events
    state.close()


def main():
    from docopt import docopt
    args = docopt(__doc__)
    set_lol(args['--lol'])

    import locale
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    if args['--clean']:
        try:
            remove(statefile)
            log.info(f"successfully removed {statefile}, setting init to True")
            args['--init'] = True
        except Exception as e: log.error(f"cannot remove {statefile}: {e}")
    # always perform an init after a clean!
    offset = timedelta(days=int(args['--days']),
                       hours=int(args['--hours']),
                       minutes=int(args['--minutes'])) # every day at 12:30
    update(offset,init=args['--init'], mock=args['--mock'])

if __name__ == "__main__":
    main()
