{ pkgs, ... }:
let

  template-karlsunruh = pkgs.stdenv.mkDerivation {
    name = "karlsunruh";
    src = pkgs.fetchgit {
      url = "https://git.project-insanity.org/onny/eintopf-karlsunruh.git";
      rev = "0c2a36574260da70da80b379d7475af7b29849c9";
      hash = "sha256-GPKlqpztl4INqVyz/4y/vVrkDPHA3rIxtUZB9LNZ96c=";
    };
    dontBuild = true;
    installPhase = ''
      cp -r . $out/
    '';
  };

in
{

  services.eintopf = {
    enable = true;
    settings = {
      EINTOPF_THEMES = "eintopf,${template-karlsunruh}";
      EINTOPF_ADMIN_PASSWORD = "foobar23";
      EINTOPF_ADMIN_EMAIL = "onny@project-insanity.org";
    };
  };

}
