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
environment.etc."mail-quota-warning-secrets.yml".text = ''
accounts:
  - name: Sales
    imap_server: mail.example.com
    imap_port: 993
    username: sales@example.com
    password: secret

  - name: Support
    imap_server: mail.example.com
    imap_port: 993
    username: support@example.com
    password: secret

mail:
  smtp_server: mail.example.com
  smtp_port: 587
  smtp_username: monitoring@example.com
  smtp_password: secret
  from_address: monitoring@example.com
  recipients:
    - admin1@example.com
    - admin2@example.com
'';

services.mail-quota-warning = {
  enable = true;
  settings = {
    CHECK_INTERVAL_DAYS = 7;
    QUOTA_WARNING_THRESHOLD_PERCENT = 80;    
  };
  secrets = [ /etc/mail-quota-warning-secrets.yml ];
};
```

Replace setting variables according to your setup.

### From source

```
cd mail-quota-warning
nix develop
export CHECK_INTERVAL_DAYS=7
export QUOTA_WARNING_THRESHOLD_PERCENT=80
nix run
```
