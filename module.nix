{config, lib, pkgs, ...}:

with lib;

let

  cfg = config.services.eintopf-radar-sync;

in 
  {

    options = {
      services.eintopf-radar-sync = {

        enable = mkOption {
          type = types.bool;
          default = false;
          description = ''
            Enable eintopf-radar-sync daemon.
          '';
        };

        settings = mkOption {
          type = types.submodule {
            freeformType = jsonFormat.type;
            options = {
              eintopfUrl = mkOption {
                default = "";
                type = types.str;
                description = ''
		  Base URL of the target Eintopf host.
                '';
              };
              radarGroupId = mkOption {
                default = "";
                type = types.str;
                description = ''
		  Radar group ID which events to sync.
                '';
              };
	    };
          };
          default = {};
          description = ''
            Extra options which should be used by the Radar sync script.
          '';
          example = literalExpression ''
            {
              eintopfUrl = "eintopf.info";
    	      radarGroupId = "436012";
            }
          '';
        };

        secretFile = mkOption {
          type = types.nullOr types.str;
          default = null;
          description = ''
            Secret options which will be appended to the Radar sync config, for example
            `{"redis":{"password":"secret"}}`.
          '';
        };

      };
    };

    config = mkIf cfg.enable {

      systemd.services."eintopf-radar-sync" = {
        description = "eintopf-radar-sync script";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        environment.PYTHONUNBUFFERED = "1";
        serviceConfig = {
	  Type = "simple";
          ExecStart = lib.getExe pkgs.eintopf-radar-sync;
          Restart = "on-failure";
	  DynamicUser = true;
          RestartSec = 30;
	  # TODO hardening
	  # TODO settings
        };
        restartIfChanged = true;
      };

    };

    meta = {
      maintainers = with lib.maintainers; [ onny ];
    };

  }

