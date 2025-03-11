{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-24.11";
    # Required for multi platform support
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      rec {
        devShell = pkgs.mkShell {
          packages =
            with pkgs;
            with python3Packages;
            [
              python
              requests
              beautifulsoup4
              pyyaml
            ];
        };

        packages = flake-utils.lib.flattenTree {
          eintopf-radar-sync = pkgs.python3Packages.buildPythonApplication {
            pname = "eintopf-radar-sync";
            version = "0.0.1";
            format = "other";

            src = self;

            dependencies = with pkgs.python3Packages; [
              python
              requests
              beautifulsoup4
              pyyaml
            ];

            installPhase = ''
              install -Dm755 ${./eintopf-radar-sync.py} $out/bin/eintopf-radar-sync
            '';
          };
        };

        defaultPackage = packages.eintopf-radar-sync;

        # eintopf-radar-sync service module
        nixosModule = (import ./module.nix);
      }
    );
}
