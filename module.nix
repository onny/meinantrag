{
  config,
  lib,
  pkgs,
  ...
}:
let

  cfg = config.services.fragify;

in
{

  options = {
    services.fragify = {

      enable = lib.mkEnableOption "Fragify web app";

    };
  };

  config = lib.mkIf cfg.enable {

    services.uwsgi = {
      enable = true;
      plugins = [ "python3" ];

      instance = {
        type = "emperor";
        vassals = {
          fragify = {
            type = "normal";
            chdir = "/";

            module = "fragify_wsgi:app";

            socket = "${config.services.uwsgi.runDir}/fragify.sock";
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
              "PYTHONPATH=${pkgs.fragify}/share/fragify:${pkgs.fragify.pythonPath}"
              "FRAGIFY_TEMPLATES_DIR=${pkgs.fragify}/share/fragify/templates"
              "FRAGIFY_STATIC_DIR=${pkgs.fragify}/share/fragify/assets"
            ];

            settings = {
              "static-map" = "/static=${pkgs.fragify}/share/fragify/assets";
            };
          };
        };
      };
    };

    # Ensure fragify user and group exist
    users.users.fragify = {
      isSystemUser = true;
      group = "fragify";
      description = "fragify web application user";
    };

    users.groups.fragify = { };
  };

  meta = {
    maintainers = with lib.maintainers; [ onny ];
  };
}
