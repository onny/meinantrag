{config, lib, pkgs, ...}:
let

  cfg = config.services.mail-quota-warning;

in 
  {

    options = {
      services.mail-quota-warning = {

        enable = lib.mkOption {
          type = lib.types.bool;
          default = false;
          description = ''
            Enable mail-quota-warning daemon.
          '';
        };

        settings = lib.mkOption {
          type = lib.types.submodule {
            freeformType = with lib.types; attrsOf anything;
            options = {
              CHECK_INTERVAL_DAYS = lib.mkOption {
                default = 7;
                type = lib.types.int;
                description = ''
                  Interval of days in which a warning message will be
                  delivered.
                '';
              };
              QUOTA_WARNING_THRESHOLD_PERCENT = lib.mkOption {
                default = 80;
                type = lib.types.int;
                description = ''
		              Threshold of used mailbox space in percent after which
                  a warning message will be delivered.
                '';
              };
	    };
          };
          default = {};
          description = ''
            Extra options which should be used by the mailbox quota warning script.
          '';
          example = lib.literalExpression ''
            {
              CHECK_INTERVAL_DAYS = 7;
    	        QUOTA_WARNING_THRESHOLD_PERCENT = 80;
            }
          '';
        };

        secretFile = lib.mkOption {
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

      systemd.services."mail-quota-warning" = {
        description = "mail-quota-warning script";
        after = [ "network.target" ];
        wants = [ "network-online.target" ];
        environment = {
	  PYTHONUNBUFFERED = "1";
	} // lib.mapAttrs (_: v: toString v) cfg.settings;
        serviceConfig = {
	  Type = "simple";
          ExecStart = lib.getExe pkgs.mail-quota-warning;

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
        } // lib.optionalAttrs (cfg.secretFile != [ ]) {
	  EnvironmentFile = cfg.secretFile;
	};
      };

      systemd.timers.mail-quota-warning = {
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

