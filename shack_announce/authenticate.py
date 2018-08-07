from docopt import docopt
from getpass import getpass
import os.path


def auth_mastodon(mail="cube8cup@gmail.com", url="https://chaos.social"):
    pw = getpass("Mastodon PW:")
    usercred = "shack-publisher_usercred.secret"
    clientcred = "shack-publisher_clientcred.secret"
    if os.path.isfile(usercred):
        print(f"{usercred} already exists, skipping mastodon auth")
        return

    from mastodon import Mastodon

    Mastodon.create_app(
        "shack-publisher", api_base_url="https://chaos.social", to_file=clientcred
    )

    mastodon = Mastodon(client_id=clientcred, api_base_url="https://chaos.social")
    mastodon.log_in("cube8cup@gmail.com", pw, to_file=usercred)
    print(f"Successfully created '{clientcred}' and '{usercred}'")


def main():
    auth_mastodon()


if __name__ == "__main__":
    main()
