{
  description = "eintopf-radar-sync package and service";

  inputs.nixpkgs.url = "nixpkgs/nixos-24.11";

  outputs = { self, nixpkgs }:
  let
    systems = [ "x86_64-linux" "i686-linux" "aarch64-linux" ];
    forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
    # Import nixpkgs with our overlay for each system.
    nixpkgsFor = forAllSystems (system:
      import nixpkgs {
        inherit system;
        overlays = [ self.overlay ];
      }
    );
  in {
    overlay = final: prev: {
      eintopf-radar-sync = with final; python3Packages.buildPythonApplication {
        pname = "eintopf-radar-sync";
        version = "0.0.1";
        format = "other";

        src = self;

        dependencies = with python3Packages; [
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

    packages = forAllSystems (system: {
      inherit (nixpkgsFor.${system}) eintopf-radar-sync;
    });

    defaultPackage = forAllSystems (system: self.packages.${system}.eintopf-radar-sync);

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
    in pkgs.mkShell {
      buildInputs = with pkgs; with python3Packages; [
        python
        requests
        beautifulsoup4
        pyyaml
      ];
    });

    # eintopf-radar-sync service module
    nixosModule = (import ./module.nix);
  };
}
