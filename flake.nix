{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-24.05";
    # Required for multi platform support
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        start =
          pkgs.writeShellScriptBin "start" ''
            set -e
            ${pkgs.python3}/bin/python eintopf-sync.py
          '';
      in
      {
        devShell = pkgs.mkShell {
          packages = with pkgs; with python3Packages; [
            python3
            requests
          ];
        };

        packages = { inherit start; };
        defaultPackage = start;
      });
}

