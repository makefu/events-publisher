#! /usr/bin/env nix-shell
""" usage: doit.py [options]

Options:
    --init                   performs an initial run which will not publish all new events
    --clean                  removes the database at startup
    --mock                   mock the requests and use events.json and series.json locally
    --lol=LEVEL              set log level [Default: INFO]
    --days=D                 Offset in days when to announce an event (starting 0:00) [Default: 0]
    --hours=H                Offset in hours [Default: 11]
    --minutes=M              Offset in minutes [Default: 30]
    --twitter-creds=FILE     Path to the twitter credential file
    --mastodon-creds=FILE    Path to the mastodon credential file
    --facebook-creds=FILE    Path to the facebook credential file
    --state=FILE             Path to state file [Default: state.db]

By default we announce a new event at 12:30 the day before
"""


from os import remove
import requests
import shelve
import logging
from random import choice

log = logging.getLogger("cli")


def set_lol(lol):
    numeric_level = getattr(logging, lol.upper(), None)
    if not isinstance(numeric_level, int):
        raise AttributeError("No such log level {}".format(lol))
    logging.basicConfig(level=numeric_level)
    log.setLevel(numeric_level)


statefile = "state.db"

# from dateutil.relativedelta import *
from dateutil.rrule import *
from dateutil.parser import *
from datetime import *
import pytz

now = datetime.now(pytz.utc)

hi_list = [
    "+++ BREAKING +++",
    "FYI ->",
    "Heureka!",
    "Servus",
    "Bitte entschuldigen Sie die Störung,",
    "*Räusper*",
    "YO!",
    "Rosen sind Rot, Veilchen sind Blau,",
    "Dein Events Service informiert:",
    "Nachricht aus dem Äther:",
    "In deinem Lieblingshackerspace:",
    "Achtung, es erfolgt eine Durchsage:",
]


def within_offset(event, offset):
    event_start = parse(event["start"]).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    log.debug(f"{event['name']}: {event_start-offset} < {now} < {event_start}")
    isTomorrow = event_start - offset < now < event_start
    if isTomorrow:
        log.info(
            f"event {event['name']} starts in the next {offset} days - exactly {event_start-now} from now"
        )
        log.debug(f"{event['name']}: {event_start-offset} < {now} < {event_start}")
        return isTomorrow


def inthepast(event):
    event_end = parse(event["end"])
    log.debug(f"{event['name']}: {event_end} < {now} ")
    return event_end < now


def running(event):
    return parse(event["start"]) < now < parse(event["end"])


def days_till(event):
    return (parse(event["start"]).date() - now.date()).days


def next_series_date(event):
    return (
        rrulestr(event["rrule"], dtstart=now)
        .between(now, now + timedelta(days=365))[0]
        .astimezone()
    )


def announce(text, creds):
    log.info(f"Announcing {text}")
    try:
        announce_mastodon(text, credfile=creds["mastodon"])
        pass
    except Exception as e:
        log.error("Unable to announce to mastodon")
        log.info(f"Error Reason: {e}")

def announce_facebook(text, credfile):
    import facebook


    # graph = GraphAPI(graphApiAccessToken)
    with open(credfile) as f:
        graph = facebook.GraphAPI(access_token=json.load(f), version="2.12")
    groups = graph.get_object("me/groups")
    group_id = groups['data'][0]['id']
    graph.put_object(group_id, "feed", message=text)

def announce_mastodon(text, credfile, visibility="unlisted"):
    from mastodon import Mastodon

    mastodon = Mastodon(api_base_url="https://chaos.social", access_token=credfile)
    mastodon.status_post(text, visibility=visibility)


def update(offset, creds, state="state.db", init=False, mock=False):
    # filter all events with no ID as they are part of a series
    if mock:
        import json

        new_events = list(filter(lambda f: f["id"], json.load(open("events.json"))))
        new_series = json.load(open("series.json"))
    else:
        new_events = list(
            filter(
                lambda f: f["id"],
                requests.get("https://events-api.shackspace.de/events/").json(),
            )
        )
        new_series = requests.get("https://events-api.shackspace.de/series/").json()

    state = shelve.open(statefile)
    if not "events" in state:
        log.info("Creating new state events")
        state["events"] = new_events
        state["series"] = new_series

    events = state["events"]
    series = state["series"]
    if init:
        log.info("Will not publish the new events")
        for event in events:
            if not "announce" in event:
                event["announce"] = {}
            event["announce"]["new"] = True
            if within_offset(event, offset):
                log.debug(
                    f"event {event['name']} is within offset, setting announce to true"
                )
                event["announce"]["tomorrow"] = True
        for event in series:
            if not "announce" in event:
                event["announce"] = {}
            # find next event date logic
            next_event = next_series_date(event)
            event_start = datetime.strptime(event["start"], "%H:%M:%S")
            next_event = next_event.replace(
                hour=event_start.hour,
                minute=event_start.minute,
                second=event_start.second,
            )
            # start is actually the time when the event begins
            # we want to recycle nextday, which uses event['start'] so we override
            event["time"] = event["start"]
            event["start"] = next_event.isoformat()
            event["announce"]["new"] = True
            if within_offset(event, offset):
                log.info(
                    f"series {event['name']} is within offset, setting announce to true"
                )
                event["announce"]["tomorrow"] = True
    else:
        for event in events:
            url = f"https://events.shackspace.de/events/{event['id']}"
            hi = choice(hi_list)
            optmin = ":%M" if parse(event["start"]).minute else ""
            name = event["name"]
            # 2. August (Donnerstag), 17 Uhr
            ts = datetime.strftime(
                parse(event["start"]), f"%d. %B (%A), %-H{optmin} Uhr"
            )
            days = int(days_till(event))
            if inthepast(event):
                log.debug(f"Skipping {event['name']} because start date is in the past")
                continue
            if not "announce" in event:
                event["announce"] = {}

            if not "new" in event["announce"] or event["announce"]["new"] == False:
                log.info(f"{event['name']} has not been announced yet and is new")
                event["announce"]["new"] = True
                announce(f"{hi} Neues Event '{name}' am {ts} - {url}", creds)
            elif (
                not "tomorrow" in event["announce"]
                or event["announce"]["tomorrow"] == False
            ):
                if within_offset(event, offset):
                    log.info(
                        f"event {event['name']} is within offset and has not been announced yet"
                    )
                    event["announce"]["tomorrow"] = True
                    # announce(f"{hi} Event '{name}' Tagen am {ts} - {url}")
                    announce(
                        f"{hi} Morgen, am {ts} ist '{name}' im shackspace - {url}",
                        creds,
                    )
                else:
                    event["announce"]["tomorrow"] = False

        for event in series:
            log.debug(f"handling {event['name']}")
            hi = choice(hi_list)
            url = f"https://events.shackspace.de/series/{event['id']}"
            optmin = ":%M" if parse(event["start"]).minute else ""
            # 2. August (Donnerstag), 17 Uhr
            ts = datetime.strftime(
                parse(event["start"]), f"%d. %B (%A), %-H{optmin} Uhr"
            )

            if not "announce" in event:
                log.debug("'announce' not set, adding to event")
                event["announce"] = {}
            # find next event date logic

            next_event = next_series_date(event)
            # start is actually the time when the event begins
            # we want to recycle nextday, which uses event['start'] so we override
            if not "time" in event:
                log.debug(
                    "'time' is not in event, saving original start date to 'time' key"
                )
                event["time"] = event["start"]

            event_start = datetime.strptime(event["time"], "%H:%M:%S")
            next_event = next_event.replace(
                hour=event_start.hour,
                minute=event_start.minute,
                second=event_start.second,
            ).isoformat()

            # if series has not been announced and is new: annouce as "new series on ... at ... + link`
            if not "new" in event["announce"] or event["announce"]["new"] == False:
                log.info(f"{event['name']} has not been announced yet and is new")
                event["announce"]["new"] = True
                announce(
                    f"{hi} Neue Serie '{name}', nächster Termin {ts} - {url}", creds
                )

            # if a new date has been calculated, reset the annouce flag
            if event["start"] != next_event:
                log.info(f"start date changed from {event['start']} to {next_event}")
                event["start"] = next_event
                event["announce"]["tomorrow"] = False

            # if series is in the next day and has not been announced: announce as `tomorrow at ... starts`
            if (
                "tomorrow" not in event["announce"]
                or event["announce"]["tomorrow"] == False
            ) and within_offset(event, offset):
                log.info(
                    f"series {event['name']} is within offset, setting announce to true"
                )
                announce(
                    f"{hi} Morgen, am {ts} ist '{name}' im shackspace - {url}", creds
                )
                event["announce"]["tomorrow"] = True

    state["events"] = events
    state["series"] = series
    state.close()


def main():
    from docopt import docopt

    args = docopt(__doc__)
    set_lol(args["--lol"])

    import locale

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
    statefile = args["state"]
    if args["--clean"]:
        try:
            remove()
            log.info(f"successfully removed {statefile}, setting init to True")
            args["--init"] = True
        except Exception as e:
            log.error(f"cannot remove {statefile}: {e}")
    # always perform an init after a clean!
    creds = {"mastodon": args["--mastodon-creds"], "twitter":
            args["--twitter-creds"], "facebook": args['--facebook-creds']}
    offset = timedelta(
        days=int(args["--days"]),
        hours=int(args["--hours"]),
        minutes=int(args["--minutes"]),
    )  # every day at 12:30
    update(offset, creds, state=statefile, init=args["--init"], mock=args["--mock"])


if __name__ == "__main__":
    main()
