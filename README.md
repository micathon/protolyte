# protolyte
This Protolyte project is the prototype of a more ambitious project called Picrolyte, which attempts to monetize Protolyte functionality. To launch Protolyte, visit localhost:6996 in your browser after running its Python script.

Every image is stored in either an image folder (called a picro, which may contain multiple images) or a folder named "$" contained in an image folder. All picros (rows of pictures) are stored in bytros. The Protolyte database consists of a list of bytros. Only one bytro is stored in RAM at any given time

Images are displayed in either a grid of 3 rows by 6 columns, or a single large image. The image grids corresponding to picros are called grid inners. The grids corresponding to "$" subfolders of picros are called grid cores. The grids corresponding to the bytros in the database are called grid outers.
