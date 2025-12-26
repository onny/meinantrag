{
  description = "meinantrag package and service";

  inputs.nixpkgs.url = "nixpkgs/nixos-25.11";

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
      meinantrag = with final; python3Packages.buildPythonApplication rec {
        pname = "meinantrag";
        version = "0.0.2";
        format = "other";

        src = self;

        dontBuild = true;

        dependencies = with python3Packages; [
          falcon
          requests
          jinja2
          google-generativeai # Dependency for Gemini API
          grpcio              # Required by google-generativeai
          reportlab           # Dependency for PDF generation
          python-docx          # Dependency for Word document generation
        ];

        installPhase = ''
          install -Dm755 ${./meinantrag.py} $out/bin/meinantrag
          mkdir -p $out/share/meinantrag
          cp -r ${./templates} $out/share/meinantrag/templates
          # Provide a WSGI entry file for uWSGI to load
          install -Dm644 ${./meinantrag.py} $out/share/meinantrag/meinantrag_wsgi.py
          # Install built assets if present
          if [ -d ./assets ]; then
            cp -r ./assets $out/share/meinantrag/
          fi
        '';

        passthru.pythonPath = python3Packages.makePythonPath dependencies;

        meta.mainProgram = "meinantrag";
      };
    };

    packages = forAllSystems (system: {
      inherit (nixpkgsFor.${system}) meinantrag;
    });

    defaultPackage = forAllSystems (system: self.packages.${system}.meinantrag);

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs { inherit system; overlays = [ self.overlay ]; };
    in pkgs.mkShell {
      buildInputs = with pkgs; with python3Packages; [
        python
        requests
        beautifulsoup4
      ];
    });

    # meinantrag service module
    nixosModule = (import ./module.nix);
  };
}
