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
    --creds=FILE             Path to credentials file [Default: creds.json]
    --state=FILE             Path to state file [Default: state.db]

By default we announce a new event at 12:30 the day before
"""
import json
from os import remove
import requests
import logging
from random import choice
import sys
from .announce import fb, toot, matrix, twitter

log = logging.getLogger("daemon")


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

now = datetime.now(pytz.timezone("Europe/Berlin"))

hi_list = [
    "+++ BREAKING +++",
    "FYI ->",
    "Heureka!",
    "Aufgepasst",
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
    # log.debug(f"{event['name']}: {event_end} < {now} ")
    return event_end < now


def running(event):
    return parse(event["start"]) < now < parse(event["end"])


def days_till(event):
    return (parse(event["start"]).date() - now.date()).days


def next_series_date(event):
    return rrulestr(event["rrule"], dtstart=now).between(
        now, now + timedelta(days=365)
    )[0]


def announce(text, creds):

    log.info(f"Announcing {text}")
    for name,cred in creds.get('mastodon',{}).items():
        try:
            toot.announce(text, cred=cred)
            log.info(f"Announced to {name} -> {cred['url']}")
        except Exception as e:
            log.error(f"Unable to announce to mastodon {name} {cred}")
            log.info(f"Error Reason: {e}")

    try:
        fb.announce(text, cred=creds["facebook"])
        log.info(f"Announced to facebook")
    except Exception as e:
        log.error("Unable to announce to facebook")
        log.info(f"Error Reason: {e}")

    try:
        matrix.announce(text, cred=creds["matrix"])
        log.info(f"Announced to matrix")
    except Exception as e:
        log.error("Unable to announce to matrix")
        log.info(f"Error Reason: {e}")

    try:
        twitter.announce(text, cred=creds["twitter"])
        log.info(f"Announced to twitter")
    except Exception as e:
        log.error("Unable to announce to twitter")
        log.info(f"Error Reason: {e}")



def update(offset, creds, statefile="state.db", init=False, mock=False):
    # filter all events with no ID as they are part of a series
    if mock:
        log.debug("using mocked input")
        new_events = list(filter(lambda f: f["id"] and not inthepast(f), json.load(open("events.json"))))
        new_series = json.load(open("series.json"))
    else:
        log.debug("using events-api input")
        new_events = list(
            filter(
                lambda f: f["id"] and not inthepast(f),
                requests.get("https://events-api.shackspace.de/events/").json(),
            )
        )
        new_series = requests.get("https://events-api.shackspace.de/series/").json()
    try:
        state = json.load(open(statefile))
    except:
        state = {}

    if not "events" in state:
        log.info("Creating new state events")
        state["events"] = new_events
        state["series"] = new_series


    events = state["events"]
    series = state["series"]
    # add new events
    for ne in new_events:
        for e in events:
            if e["id"] == ne["id"]:
                log.debug("found old info, updating event info")
                e.update(ne)
                break
        else:
            log.info(f"new event {ne['id']} not found in old events, must be new")
            events.append(ne)

    # add new series
    for ns in new_series:
        for s in series:
            if s["id"] == ns["id"]:
                # s.update(ns) - TODO: s['start'] breaks the current logic (override start to the next event)
                s['time'] = ns['start']
                s['rrule'] = ns['rrule']
                s['deleted'] = ns['deleted']
                break
        else:
            log.info(f"new series with id {ns['id']} found, adding")
            series.append(ns)


    if init:
        log.info("Will not publish the new events")
        for e in events:
            if "announce" not in e:
                e["announce"] = {"new": True, "tomorrow": False}
            if within_offset(e, offset):
                log.debug(f"event {e['name']} is within offset")
                e["announce"]["tomorrow"] = True
        for s in series:
            if "announce" not in s:
                s["announce"] = {"new": True, "tomorrow": False}
            next_event = next_series_date(s)
            try:
                event_start = datetime.strptime(s["start"], "%H:%M:%S")
            except:
                event_start = datetime.strptime(s["time"], "%H:%M:%S")
            next_event = (
                next_event.replace(
                    hour=event_start.hour,
                    minute=event_start.minute,
                    second=event_start.second,
                    tzinfo=None,
                )
                .astimezone(pytz.timezone("Europe/Berlin"))
                .isoformat()
            )
            # start is actually the time when the event begins
            # we want to recycle nextday, which uses event['start'] so we override
            s["time"] = s["start"]
            s["start"] = next_event
            if within_offset(s, offset):
                log.info(f"series {s['name']} is within offset")
                s["announce"]["tomorrow"] = True

    # update events / optionally announce
    for e in filter(lambda e: not e['deleted'], events):
        if "announce" not in e:
            e["announce"] = {"new": False, "tomorrow": False}
        log.debug(f"in announce for event {e['name']}, id {e['id']}, announce {e['announce']}")
        hi = choice(hi_list)
        # 2. August (Donnerstag), 17 Uhr
        days = int(days_till(e))
        if inthepast(e):
            log.debug(f"Skipping {e['name']} because start date is in the past")
            continue

        url = f"https://events.shackspace.de/events/{e['id']}"
        name = e["name"]
        optmin = ":%M" if parse(e["start"]).minute else ""
        ts = datetime.strftime(parse(e["start"]), f"%d. %B (%A), %-H{optmin} Uhr")

        if not e["announce"].get("new", False):
            log.info(f"{e['name']} has not been announced yet and is new")
            announce(f"{hi} Neues Event '{name}' am {ts} - {url}", creds)
            e["announce"]["new"] = True
        elif (not e["announce"]["tomorrow"]) and within_offset(e, offset):
            log.info(
                f"event {e['name']} is within offset and has not been announced yet"
            )
            e["announce"]["tomorrow"] = True
            announce(f"{hi} Morgen, am {ts} ist '{name}' im shackspace - {url}", creds)

    for s in filter(lambda s: not s['deleted'], series):
        log.debug(s)
        log.debug(f"in announce for series {s['name']}, id {s['id']}")
        hi = choice(hi_list)
        url = f"https://events.shackspace.de/series/{s['id']}"

        for ns in new_series:
            if s["id"] == ns["id"]:
                log.debug(
                    "found series with same id in new events, updating and keeping old start date"
                )
                last_event = s["start"]
                try:
                    datetime.strptime(s["start"], "%H:%M:%S")
                    s["time"] = ns["start"]
                except:
                    pass
                s.update(ns)
                s["start"] = last_event
                break
        else:
            log.info("event not found in new events, skipping")
            continue

        if "announce" not in s:
            s["announce"] = {"new": False, "tomorrow": False}
        # find next event date logic

        # 2. August (Donnerstag), 17 Uhr
        name = s["name"]

        next_event = next_series_date(s)
        # start is actually the time when the event begins
        # we want to recycle nextday, which uses event['start'] so we override
        if "time" not in s:
            log.debug(
                "'time' is not in series, saving original start date to 'time' key"
            )
            s["time"] = s["start"]
        try:
            event_start = datetime.strptime(s["start"], "%H:%M:%S")
        except:
            event_start = datetime.strptime(s["time"], "%H:%M:%S")
        next_event = (
            next_event.replace(
                hour=event_start.hour,
                minute=event_start.minute,
                second=event_start.second,
                tzinfo=None,
            )
            .astimezone(pytz.timezone("Europe/Berlin"))
            .isoformat()
        )

        optmin = ":%M" if parse(next_event).minute else ""
        ts = datetime.strftime(parse(next_event), f"%d. %B (%A), %-H{optmin} Uhr")
        # if series has not been announced and is new: annouce as "new series on ... at ... + link`
        if not s["announce"].get("new", False):
            log.info(f"{s['name']} has not been announced yet and is new")
            s["announce"]["new"] = True
            announce(f"{hi} Neue Serie '{name}', nächster Termin {ts} - {url}", creds)

        # if a new date has been calculated, reset the annouce flag
        if s["start"] != next_event:
            log.info(f"start date changed from {s['start']} to {next_event}")
            s["start"] = next_event
            s["announce"]["tomorrow"] = False
        else:
            log.debug(f"start date stays the same {next_event}")

        # if series is in the next day and has not been announced: announce as `tomorrow at ... starts`
        is_announced = s["announce"].get("tomorrow", False)
        is_next = within_offset(s, offset)
        log.debug(
            f"Event is announced?: {is_announced} ({s['announce']}), event tomorrow?: {is_next}"
        )
        if not is_announced and is_next:
            log.info(f"series {s['name']} is within offset, setting announce to true")
            announce(f"{hi} Morgen, am {ts} ist '{name}' im shackspace - {url}", creds)
            s["announce"]["tomorrow"] = True
        else:
            log.debug(f"will NOT announce {s['name']}")

    state["events"] = events
    state["series"] = series
    with open(statefile, "w+") as f:
        json.dump(state, f)


def main():
    from docopt import docopt

    args = docopt(__doc__)
    set_lol(args["--lol"])

    import locale

    locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
    statefile = args["--state"]
    if args["--clean"]:
        try:
            remove(statefile)
            log.info(f"successfully removed {statefile}, setting init to True")
            args["--init"] = True
        # always perform an init after a clean!
        except Exception as e:
            log.error(f"cannot remove {statefile}: {e}")
    with open(args["--creds"]) as f:
        creds = json.load(f)
    offset = timedelta(
        days=int(args["--days"]),
        hours=int(args["--hours"]),
        minutes=int(args["--minutes"]),
    )  # every day at 12:30
    log.debug(f"args: {args}")
    update(offset, creds, statefile=statefile, init=args["--init"], mock=args["--mock"])


if __name__ == "__main__":
    main()
