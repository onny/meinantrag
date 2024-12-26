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

      };
    };

    config = mkIf cfg.enable {

      systemd.services."eintopf-radar-sync" = {
        description = "eintopf-radar-sync script";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        environment.PYTHONUNBUFFERED = "1";
        serviceConfig = {
          ExecStart = "${pkgs.iwd-autocaptiveauth}/bin/iwd-autocaptiveauth --profileDir ${pkgs.iwd-autocaptiveauth}/profiles";
          Restart = "on-failure";
          User = "iwd-autocaptiveauth";
          RestartSec = 30;
          WorkingDirectory = ''${pkgs.iwd-autocaptiveauth}/'';
        };
        restartIfChanged = true;
      };

    };

    meta = {
      maintainers = with lib.maintainers; [ onny ];
    };

  }

