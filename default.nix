{ pkgs ? import <nixpkgs> {} }:
pkgs.python3Packages.buildPythonPackage rec {
  pname = "shack_announce";
  version = "0.0.5";
  propagatedBuildInputs = with pkgs.python3Packages; [
    ( callPackage ./mastodon.nix {} )
    requests twitter docopt dateutil pytz praw
    ( callPackage ./black.nix {} )
    ( callPackage ./facebook.nix {} )
  ];
  src = ./.;
  #shellHook =''
  #  HISTFILE="${toString ./.}/.histfile"
  #'' ;
}