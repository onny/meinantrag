{
  description = "fragify package and service";

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
      fragify = with final; python3Packages.buildPythonApplication {
        pname = "fragify";
        version = "0.0.1";
        format = "other";

        src = self;

        propagatedBuildInputs = with python3Packages; [ falcon requests jinja2 ];

        installPhase = ''
          install -Dm755 ${./fragify.py} $out/bin/fragify
          mkdir -p $out/share/fragify
          cp -r ${./templates} $out/share/fragify/
          # Provide a WSGI entry file for uWSGI to load
          install -Dm644 ${./fragify.py} $out/share/fragify/fragify_wsgi.py
          # Install built assets if present
          if [ -d ./assets ]; then
            cp -r ./assets $out/share/fragify/
          fi
        '';

        passthru.pythonPath = python3Packages.makePythonPath propagatedBuildInputs;

        meta.mainProgram = "fragify";
      };
    };

    packages = forAllSystems (system: {
      inherit (nixpkgsFor.${system}) fragify;
    });

    defaultPackage = forAllSystems (system: self.packages.${system}.fragify);

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
    in pkgs.mkShell {
      buildInputs = with pkgs; with python3Packages; [
        python
        requests
        beautifulsoup4
      ];
    });

    # fragify service module
    nixosModule = (import ./module.nix);
  };
}
