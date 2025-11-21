{
  config,
  lib,
  pkgs,
  ...
}:
let

  cfg = config.services.meinantrag;

in
{

  options = {
    services.meinantrag = {

      enable = lib.mkEnableOption "MeinAntrag web app";

    };
  };

  config = lib.mkIf cfg.enable {

    services.uwsgi = {
      enable = true;
      plugins = [ "python3" ];

      instance = {
        type = "emperor";
        vassals = {
          meinantrag = {
            type = "normal";
            chdir = "/";

            module = "meinantrag_wsgi:app";

            socket = "${config.services.uwsgi.runDir}/meinantrag.sock";
            "chmod-socket" = "660";

            umask = "0077";
            vacuum = true;
            master = true;
            processes = 2;
            threads = 2;
            harakiri = 60;
            "buffer-size" = 65535;
            need-app = true;
            "no-orphans" = true;

            env = [
              "PYTHONPATH=${pkgs.meinantrag}/share/meinantrag:${pkgs.meinantrag.pythonPath}"
              "MEINANTRAG_TEMPLATES_DIR=${pkgs.meinantrag}/share/meinantrag/templates"
              "MEINANTRAG_STATIC_DIR=${pkgs.meinantrag}/share/meinantrag/assets"
            ];

            settings = {
              "static-map" = "/static=${pkgs.meinantrag}/share/meinantrag/assets";
            };
          };
        };
      };
    };

    # Ensure meinantrag user and group exist
    users.users.meinantrag = {
      isSystemUser = true;
      group = "meinantrag";
      description = "meinantrag web application user";
    };

    users.groups.meinantrag = { };
  };

  meta = {
    maintainers = with lib.maintainers; [ onny ];
  };
}
