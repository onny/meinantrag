# Fragify

Eine einfache Web-Anwendung, um vorausgefüllte Links für Anfragen bei [FragDenStaat.de](https://fragdenstaat.de) zu generieren, die du an Freund:innen schicken kannst.

## Was ist Fragify?

Fragify ist ein webbasiertes Tool, das es dir ermöglicht, schnell und einfach Anfragen bei deutschen Behörden über das Informationsfreiheitsportal FragDenStaat.de zu erstellen. Du kannst:

- Nach Behörden suchen und auswählen
- Betreff und Inhalt der Anfrage vorausfüllen
- Einen fertigen Link generieren, der alle Informationen enthält
- Den Link mit anderen teilen, die dann nur noch auf "Senden" klicken müssen

## Installation

### NixOS

Füge das Modul zu deiner `flake.nix` hinzu:

```nix
{
  inputs = {
    fragify.url = "git+https://git.project-insanity.org/onny/fragify.git";
    [...]
  };

  outputs = {self, nixpkgs, ...}@inputs: {

    nixosConfigurations.tuxzentrale = inputs.nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs.inputs = inputs;
      modules = [
        inputs.fragify.nixosModule

        ({ pkgs, ... }:{

          nixpkgs.overlays = [
            inputs.fragify.overlay
          ];

        })

        ./configuration.nix

      ];
    };
  };
}
```

Füge dies zu deiner `configuration.nix` hinzu:

```nix
services.fragify = {
  enable = true;
  settings = {
    # Konfiguration hier
  };
};
```

### Von der Quelle

```bash
cd fragify
nix develop
nix run
```

Öffne dann deinen Browser und navigiere zu: http://localhost:8000

## Verwendung

1. **Behörde auswählen**: Suche und wähle die gewünschte Behörde aus dem Dropdown-Menü
2. **Betreff eingeben**: Gib einen aussagekräftigen Betreff für deine Anfrage ein
3. **Anfrage beschreiben**: Beschreibe detailliert, welche Dokumente oder Informationen du anfragen möchtest
4. **Link generieren**: Klicke auf "Anfrage Link generieren"
5. **Link teilen**: Kopiere den generierten Link und teile ihn mit anderen

## Technische Details

- **Framework**: Falcon (Python)
- **Frontend**: Bootstrap 5 mit modernem Design
- **API**: Integration mit der FragDenStaat.de API
- **Styling**: Responsive Design mit Gradient-Hintergrund

## API-Integration

Fragify nutzt die offizielle [FragDenStaat.de API](https://fragdenstaat.de/api/) um:

- Behörden zu durchsuchen
- Links zu generieren, die das Anfrage-Formular vorausfüllen
- Die korrekte URL-Struktur von FragDenStaat.de zu verwenden

## Entwicklung

### Lokale Entwicklung

```bash
# Entwicklungsumgebung starten
nix develop

# Anwendung starten
python fragify.py
```

### Abhängigkeiten

- Python 3.8+
- Falcon (Web-Framework)
- Requests (HTTP-Client)

## Lizenz

Dieses Projekt steht unter der gleichen Lizenz wie FragDenStaat.de.

## Beitragen

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## Links

- [FragDenStaat.de](https://fragdenstaat.de) - Das Hauptportal
- [FragDenStaat API](https://fragdenstaat.de/api/) - API-Dokumentation
- [Informationsfreiheitsgesetz](https://fragdenstaat.de/informationsfreiheit/) - Rechtliche Grundlagen
