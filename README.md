# eintopf-radar-sync
Small script to autologin to public wifis or test hotspots!

> Do not use this in production or against real public access points, since
> automatically logging in will violate most of the terms of use. The useage of
> this software is for development or research purpose only.

## Installation

### NixOS

Add the module to your `flake.nix`:

```nix
{
  inputs = {
    iwd-autocaptiveauth.url = "git+https://git.project-insanity.org/onny/py-iwd-autocaptiveauth.git";
    [...]
  };

  outputs = {self, nixpkgs, ...}@inputs: {

    nixosConfigurations.tuxzentrale = inputs.nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs.inputs = inputs;
      modules = [
        inputs.iwd-autocaptiveauth.nixosModule

        ({ pkgs, ... }:{

          nixpkgs.overlays = [
            inputs.iwd-autocaptiveauth.overlay
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
services.iwd-autocaptiveauth.enable = true;
```

### From source

This script requires the program
[hyperpotamus](https://github.com/pmarkert/hyperpotamus) as a dependency. As
network manager, only
[iwd](https://git.kernel.org/pub/scm/network/wireless/iwd.git/) is supported.
Further you might need to install the Python modules ``python-dbus`` and
``gobject``.

Just run ``python iwd-autocaptiveauth.py``.

## Configuration
The ``profiles`` directory contains small scripts which will perform the
http authentication process using ``hyperpotamus``. The filename should match
the ESSID of the wifi network.

Feel free to submit your profiles to this Gitlab repository!

