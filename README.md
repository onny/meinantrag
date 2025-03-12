# eintopf-radar-sync
Small script to sync events of an radar.quad.net group to a specific Eintopf
instance.

## Installation

### NixOS

Add the module to your `flake.nix`:

```nix
{
  inputs = {
    eintopf-radar-sync.url = "git+https://git.project-insanity.org/onny/eintopf-radar-sync.git";
    [...]
  };

  outputs = {self, nixpkgs, ...}@inputs: {

    nixosConfigurations.tuxzentrale = inputs.nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs.inputs = inputs;
      modules = [
        inputs.eintopf-radar-sync.nixosModule

        ({ pkgs, ... }:{

          nixpkgs.overlays = [
            inputs.eintopf-radar-sync.overlay
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
environment.etc."eintopf-radar-sync-secrets".text = ''
EINTOPF_AUTHORIZATION_TOKEN=foobar23
'';

services.eintopf-radar-sync = {
  enable = true;
  settings = {
    EINTOPF_URL = "https://karlsunruh.eintopf.info";
    RADAR_GROUP_ID = "436012";
  };
  secrets = [ /etc/eintopf-radar-sync-secrets ];
};
```

Replace setting variables according to your setup.

Get the authorization token through login request in the Eintopf
Swagger api interface, for example
https://karlsunruh.project-insanity.org/api/v1/swagger#/auth/login

### From source

```
cd eintopf-radar-sync
nix develop
export EINTOPF_URL = "https://karlsunruh.eintopf.info"
export EINTOPF_AUTHORIZATION_TOKEN = "secret key"
export RADAR_GROUP_ID = "436012"
nix run
```
