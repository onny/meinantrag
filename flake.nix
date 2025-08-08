{
  description = "mail-quota-warning package and service";

  inputs.nixpkgs.url = "nixpkgs/nixos-25.05";

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
      mail-quota-warning = with final; python3Packages.buildPythonApplication {
        pname = "mail-quota-warning";
        version = "0.0.1";
        format = "other";

        src = self;

        dependencies = with python3Packages; [
          python
	  pyyaml
	  imaplib2
        ];

        installPhase = ''
          install -Dm755 ${./mail-quota-warning.py} $out/bin/mail-quota-warning
        '';

	meta.mainProgram = "mail-quota-warning";
      };
    };

    packages = forAllSystems (system: {
      inherit (nixpkgsFor.${system}) mail-quota-warning;
    });

    defaultPackage = forAllSystems (system: self.packages.${system}.mail-quota-warning);

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
    in pkgs.mkShell {
      buildInputs = with pkgs; with python3Packages; [
        python
        requests
        beautifulsoup4
      ];
    });

    # mail-quota-warning service module
    nixosModule = (import ./module.nix);
  };
}
