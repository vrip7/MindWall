MindWall Extension Icons
========================

Place PNG icon files here:
- icon16.png  (16x16)
- icon48.png  (48x48)
- icon128.png (128x128)

Generate from the MindWall shield logo or use the following command
to create placeholder icons with ImageMagick:

  convert -size 16x16 xc:#3b82f6 -fill white -gravity center \
    -pointsize 12 -annotate 0 "M" icons/icon16.png
  convert -size 48x48 xc:#3b82f6 -fill white -gravity center \
    -pointsize 28 -annotate 0 "M" icons/icon48.png
  convert -size 128x128 xc:#3b82f6 -fill white -gravity center \
    -pointsize 72 -annotate 0 "M" icons/icon128.png
