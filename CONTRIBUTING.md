# Contributing Guidelines

## Getting Started
- Fork & clone this repo!
- Choose a piece of content to translate.
- Start an issue for that piece of content to let others know you're working on it.
  - Scripts: title your issue as `script: ####`
  - CGs: title your issue as `cg: ####`
- Translate content.
- Commit your changes to your fork & push.
- Open a pull request on this repo
  - Make sure to reference your issue!
  - PRs should be for individual units of content. One PR should be for one
    script/CG/etc.

## Scripts
- Scenes are represented by `.json` files in the `scripts/` directory. 
  - Edit scenes with the text editor (or JSON editor) of your choice.
- Scenes consist of a series of dialogs. For each dialog:
  - The `speaker` field contains the name of the person speaking.
  - Put the translation in the `speaker_translation` field.
  - The `text` field contains the speech the person is saying.
  - Put the translation in the `text_translation` field.
  - Ignore the `internal` object.
- Text is limited to 40 characters x 2 lines for each page in a script.
  - Use a newline character (`\n`) to denote a new line.
  - ```e.g. text : "Hello!\nWorld!"``` 
- Don't forget to file an issue to let people know you are translating a piece
  of content!

## CGs
- Translate CGs & textures by editing them and saving & commiting the translated version
  into the `cgs_translated` folder. 
- Try to not change the palette of images when editing. 
- Make sure to keep the alpha channel of textures (if there is one).
- Don't forget to file an issue to let people know you are translating a piece
  of content!

