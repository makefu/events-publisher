{ pkgs ? import <nixpkgs> {} }:
let
in pkgs.mkShell rec {
  buildInputs = with pkgs.python3Packages; [
    ( callPackage ./mastodon.nix {} )
    requests twitter docopt dateutil pytz
    ( callPackage ./black.nix {} )
    ( callPackage ./facebook.nix {} )
  ];
    shellHook =''
      HISTFILE="${toString ./.}/.histfile"
    '' ;
}

