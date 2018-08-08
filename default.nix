{ pkgs, ... }:
with import <stockholm/lib>;

let
  shack-announce =  pkgs.callPackage ./package.nix {};
  home = "/var/lib/shackannounce";
  user = "shackannounce";
  creds = (toString <secrets>) + "/shack-announce.json";
in
{
  users.users.${user}= {
    uid = genid user;
    inherit home;
    createHome = true;
  };
  systemd.services.shack-announce = {
    description = "Announce shack events";
    startAt = "*:0/30";
    path = [ shack-announce ];
    serviceConfig  = {
      WorkingDirectory = home;
      User = user;
      PermissionsStartOnly = true;
      ExecStartPre = pkgs.writeDash "shack-announce-pre" ''
        set -eu
        cp ${creds} creds.json
        chown ${user} creds.json
      '';
      ExecStart = pkgs.writeDash "shack-announce" ''
        if test ! -e announce.state; then
          echo "initializing state"
          announce-daemon \
            --lol INFO \
            --creds creds.json \
            --state announce.state \
            --clean --init
        fi
        echo "Running announce"
        announce-daemon \
           --lol INFO \
           --creds creds.json \
           --state announce.state
      '';
    };
  };
}
