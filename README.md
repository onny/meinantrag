# MeinAntrag

Eine einfache Web-Anwendung, um vorausgefüllte Links für Anfragen bei [FragDenStaat.de](https://fragdenstaat.de) zu generieren, die du an Freund:innen schicken kannst.

## Was ist MeinAntrag?

MeinAntrag ist ein webbasiertes Tool, das es dir ermöglicht, schnell und einfach Anfragen bei deutschen Behörden über das Informationsfreiheitsportal FragDenStaat.de zu erstellen. Du kannst:

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
    meinantrag.url = "git+https://git.project-insanity.org/onny/meinantrag.git";
    [...]
  };

  outputs = {self, nixpkgs, ...}@inputs: {

    nixosConfigurations.tuxzentrale = inputs.nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      specialArgs.inputs = inputs;
      modules = [
        inputs.meinantrag.nixosModule

        ({ pkgs, ... }:{

          nixpkgs.overlays = [
            inputs.meinantrag.overlay
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
services.meinantrag = {
  enable = true;
};
```

### Von der Quelle

```bash
cd meinantrag
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

## Frontend-Assets (lokal statt CDN)

Die Anwendung kann CSS/JS-Assets lokal bereitstellen. Dafür werden `npm` und `gulp` benutzt.

### Bauen der Assets

```bash
# Abhängigkeiten installieren (nutzt npm ci, wenn package-lock.json existiert)
make build
# Alternativ ohne make
npm install
npm run build
```

Die gebauten Dateien landen in `assets/` und werden vom Server unter `/static/...` ausgeliefert:

- CSS: `/static/css/bootstrap.min.css`, `/static/css/select2.min.css`, `/static/css/select2-bootstrap-5-theme.min.css`
- JS: `/static/js/bootstrap.bundle.min.js`, `/static/js/jquery.min.js`, `/static/js/select2.min.js`

### Hinweis
- Stelle sicher, dass `assets/` existiert, sonst werden stattdessen CDN-Links erwartet.
- In der Entwicklungs-Serverausgabe steht: "Serving static assets from: ..." – dort solltest du den Pfad zu `assets/` sehen.

## Deployment mit Nix/uWSGI

- Das Nix-Paket installiert Templates und (falls vorhanden) `assets/` nach `$out/share/meinantrag/...`.
- Das NixOS-Modul startet uWSGI und erzeugt einen UNIX-Socket unter `unix:${config.services.uwsgi.runDir}/meinantrag.sock`.
- Die App respektiert folgende Umgebungsvariablen:
  - `MEINANTRAG_TEMPLATES_DIR` – Pfad zu den Templates
  - `MEINANTRAG_STATIC_DIR` – Pfad zu den statischen Assets (`assets/`)

Beispiel (im uWSGI-Instance Block):
```nix
services.uwsgi.instance.meinantrag = {
  env = {
    MEINANTRAG_TEMPLATES_DIR = "${pkgs.meinantrag}/share/meinantrag/templates";
    MEINANTRAG_STATIC_DIR = "${pkgs.meinantrag}/share/meinantrag/assets";
  };
};
```

## Entwicklung

### Lokale Entwicklung

```bash
# Entwicklungsumgebung starten
nix develop

# Anwendung starten
python meinantrag.py
```

### Abhängigkeiten

- Python 3.8+
- Falcon (Web-Framework)
- Requests (HTTP-Client)
- Node.js + npm (für lokale Assets)
- gulp (wird via npm-Script genutzt)

## Lizenz

Dieses Projekt steht unter der gleichen Lizenz wie FragDenStaat.de.

## Beitragen

Beiträge sind willkommen! Bitte erstelle einen Pull Request oder öffne ein Issue.

## Links

- [FragDenStaat.de](https://fragdenstaat.de) - Das Hauptportal
- [FragDenStaat API](https://fragdenstaat.de/api/) - API-Dokumentation
- [Informationsfreiheitsgesetz](https://fragdenstaat.de/informationsfreiheit/) - Rechtliche Grundlagen
