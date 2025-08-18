# mail-quota-warning

Small script to check a configured list of IMAP accounts for mailbox quota and send
a warning mail in case a specific threashold is exceeded.

## Installation

### NixOS

Add the module to your `flake.nix`:

```nix
{
  inputs = {
    mail-quota-warning.url = "git+https://git.project-insanity.org/onny/mail-quota-warning.git";
    [...]
  };

  outputs = {self, nixpkgs, ...}@inputs: {

    nixosConfigurations.tuxzentrale = inputs.nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs.inputs = inputs;
      modules = [
        inputs.mail-quota-warning.nixosModule

        ({ pkgs, ... }:{

          nixpkgs.overlays = [
            inputs.mail-quota-warning.overlay
          ];

        })

        ./configuration.nix

      ];
    };
  };
}
```

Add this to your `configuration.nix` file

```nix
environment.etc."eintopf-radar-sync-secrets.yml".text = ''
EINTOPF_AUTHORIZATION_TOKEN=foobar23
'';

services.mail-quota-warning = {
  enable = true;
  settings = {
    EINTOPF_URL = "https://karlsunruh.eintopf.info";
    RADAR_GROUP_ID = "436012";
  };
  secrets = [ /etc/mail-quota-warning-secrets.yml ];
};
```

Replace setting variables according to your setup.

### From source

```
cd mail-quota-warning
nix develop
export EINTOPF_URL = "https://karlsunruh.eintopf.info"
export EINTOPF_AUTHORIZATION_TOKEN = "secret key"
export RADAR_GROUP_ID = "436012"
nix run
```
