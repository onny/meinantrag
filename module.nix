{
  config,
  lib,
  pkgs,
  ...
}:
let

  cfg = config.services.mail-quota-warning;

in
{

  options = {
    services.fragify = {

      enable = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = ''
          Enable fragify web application.
        '';
      };

    };
  };

  config = lib.mkIf cfg.enable {

    systemd.services."fragify" = {
      description = "fragify web application";
      after = [ "network.target" ];
      wants = [ "network-online.target" ];
      environment = {
        PYTHONUNBUFFERED = "1";
      };
      serviceConfig = {
        Type = "simple";
        ExecStart = "${lib.getExe pkgs.fragify}";
        WorkingDirectory = "%S/fragify";
        StateDirectory = "fragify";
        User = "fragify";
        Group = "fragify";

        # hardening
        AmbientCapabilities = "";
        CapabilityBoundingSet = "";
        DevicePolicy = "closed";
        DynamicUser = false;
        LockPersonality = true;
        MemoryDenyWriteExecute = true;
        NoNewPrivileges = true;
        PrivateDevices = true;
        PrivateTmp = true;
        PrivateUsers = false;
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
        RestrictAddressFamilies = [
          "AF_INET"
          "AF_INET6"
        ];
        RestrictNamespaces = true;
        RestrictRealtime = true;
        RestrictSUIDSGID = true;
        SystemCallArchitectures = "native";
        SystemCallFilter = [
          "@system-service"
          "~@privileged"
        ];
        UMask = "0077";
      };
    };

    # Create fragify user and group
    users.users.fragify = {
      isSystemUser = true;
      group = "fragify";
      description = "fragify web application user";
    };

    users.groups.fragify = {};

  };

  meta = {
    maintainers = with lib.maintainers; [ onny ];
  };

}
