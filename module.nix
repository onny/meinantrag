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

      settings = lib.mkOption {
        type = lib.types.attrsOf lib.types.str;
        default = { };
        example = {
          MEINANTRAG_BASE_URL = "https://example.com";
          GOOGLE_GEMINI_API_KEY = "file:/run/secrets/gemini_api_key";
        };
        description = ''
          Additional environment variables to pass to the MeinAntrag service.
          Values starting with "file:" will be read from the specified path.
          For secrets with systemd LoadCredential, use the credentials option instead.
        '';
      };

      credentials = lib.mkOption {
        type = lib.types.attrsOf lib.types.str;
        default = { };
        example = {
          GOOGLE_GEMINI_API_KEY = "/run/secrets/gemini_api_key";
        };
        description = ''
          Credentials to pass to the MeinAntrag service.
          Maps environment variable names to file paths containing the secret values.
          These are loaded via systemd's LoadCredential mechanism.
          The Python app will automatically read the value from the file.
        '';
      };

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
            ] ++ (lib.mapAttrsToList (name: value: "${name}=${value}") cfg.settings)
              ++ (lib.mapAttrsToList (name: _: "${name}=file:/run/credentials/uwsgi.service/${name}") cfg.credentials);

            settings = {
              "static-map" = "/static=${pkgs.meinantrag}/share/meinantrag/assets";
            };
          };
        };
      };
    };

    # Load credentials via systemd's LoadCredential mechanism
    systemd.services.uwsgi.serviceConfig.LoadCredential =
      lib.mapAttrsToList (key: value: "${key}:${value}") cfg.credentials;

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
