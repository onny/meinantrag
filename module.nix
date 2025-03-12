{config, lib, pkgs, ...}:
let

  cfg = config.services.eintopf-radar-sync;

in 
  {

    options = {
      services.eintopf-radar-sync = {

        enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = ''
            Enable eintopf-radar-sync daemon.
          '';
        };

        settings = lib.mkOption {
          type = lib.types.submodule {
            freeformType = with lib.types; attrsOf types.str;
            options = {
              EINTOPF_URL = lib.mkOption {
                default = "";
                type = lib.types.str;
                description = ''
		  Base URL of the target Eintopf host.
                '';
              };
              RADAR_GROUP_ID = lib.mkOption {
                default = "";
                type = lib.types.str;
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
          example = lib.literalExpression ''
            {
              EINTOPF_URL = "eintopf.info";
    	      RADAR_GROUP_ID = "436012";
            }
          '';
        };

        secrets = lib.mkOption {
          type = with lib.types; listOf path;
          description = ''
            A list of files containing the various secrets. Should be in the
            format expected by systemd's `EnvironmentFile` directory.
          '';
          default = [ ];
        };

        interval = lib.mkOption {
          type = lib.types.str;
          default = "*:00,30:00";
          description = ''
            How often we run the sync. Default is half an hour.
  
            The format is described in
            {manpage}`systemd.time(7)`.
          '';
        };

      };
    };

    config = lib.mkIf cfg.enable {

      systemd.services."eintopf-radar-sync" = {
        description = "eintopf-radar-sync script";
        after = [ "network.target" ];
        wants = [ "network-online.target" ];
        environment = {
	  PYTHONUNBUFFERED = "1";
	} // cfg.settings;
        serviceConfig = {
	  Type = "simple";
          ExecStart = lib.getExe pkgs.eintopf-radar-sync;
	  EnvironmentFile = [ cfg.secrets ];

          # hardening
          AmbientCapabilities = "";
          CapabilityBoundingSet = "" ;
          DevicePolicy = "closed";
          DynamicUser = true;
          LockPersonality = true;
          MemoryDenyWriteExecute = true;
          NoNewPrivileges = true;
          PrivateDevices = true;
          PrivateTmp = true;
          PrivateUsers = true;
          ProcSubset = "pid";
          ProtectClock = true;
          ProtectControlGroups = true;
          ProtectHome = true;
          ProtectHostname = true;
          ProtectKernelLogs = true;
          ProtectKernelModules = true;
          ProtectKernelTunables = true;
          ProtectProc = "invisible";
          ProtectSystem = "strict";
          RemoveIPC = true;
          RestrictAddressFamilies = [ "AF_INET" "AF_INET6" ];
          RestrictNamespaces = true;
          RestrictRealtime = true;
          RestrictSUIDSGID = true;
          SystemCallArchitectures = "native";
          SystemCallFilter = [ "@system-service" "~@privileged" ];
          UMask = "0077";
        };
      };

      systemd.timers.eintopf-radar-sync = {
        timerConfig = {
          OnCalendar = [
            ""
            cfg.interval
          ];
        };
        wantedBy = [ "timers.target" ];
      };

    };

    meta = {
      maintainers = with lib.maintainers; [ onny ];
    };

  }

