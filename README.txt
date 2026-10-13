ISORIM
======

RimWorld in 3D, through an isometric camera. Visual only: safe to add to or remove from an
existing save.

Requires Harmony (load it above IsoRim). Built for RimWorld 1.5.


CONTROLS
--------
  0          3D view on and off (also the cube button, bottom right of the screen)
  9          isometric view or straight-on view (north up)
  Q and E    turn the camera, in 45 or 90 degree steps
             (while something is picked to build, Q and E turn that instead, as usual)
  [ and ]    lower or raise the camera
  House button (bottom right): show roofs. A key for it can be set.
  Middle mouse button: drag the map.

  All keys: Options > Keyboard configuration > IsoRim.
  All settings: Options > Mod settings > IsoRim.


SETTINGS
--------
  View and camera        isometric view, turn step, camera angle, wall height
  See-through            lower walls, thin out trees and lift roofs near the pointer or
                         near your colonists
  Colour and light       colour looks, shadows, a sun that moves through the day
  Ground, water, roofs   ground and floor textures, stylised water, roof style
  What is 3D             switch any part of the 3D view off if it clashes with another mod


EXACT COLOUR GRADING (OPTIONAL)
-------------------------------
  The colour looks work out of the box. For exact grading with lookup tables (LUTs), a
  small shader has to be built once in Unity; see DEVELOPMENT.txt. Your own 1024 x 32 LUT
  strips can then be dropped into the LUTs folder.


COMPATIBILITY
-------------
  Other mods that change how pawns are drawn or how the camera works may clash. Buildings,
  animals and plants from DLC and mods without a model of their own are raised into 3D from
  their own sprites. Modded wrecks and junk are matched by name.


PROBLEMS
--------
  Switch features off one at a time under "What is 3D" to find which one causes it.
  With the game's development mode on, IsoRim writes what it found and skipped to the log.
