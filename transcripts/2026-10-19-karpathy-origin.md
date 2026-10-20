# Karpathy origin

**Session.** Cursor coordinator `bc-3b8eca37-6314-4abb-af51-4792f587b880`, 2026-10-19.
**Record.** Reconstruction from that coordinator chat. The verbatim opening message is not in this worker's log.

The biology task started from Andrej Karpathy's land-or-water map (https://x.com/karpathy/status/2105909609487872075). That prompt asks a model, one coordinate at a time, whether a point is land or water, then checks whether the answers reconstruct the globe. The same test was wanted for biology: no tools, one small question repeated across a structure, scored against a real map, and drawn so a person can see whether the model understands it.

That became Task 1. GFP's barrel is the map. Each beta-strand residue is a coordinate. Toward the chromophore or away from it is the land-or-water question. The crystal structure is the ground truth. The circular barcode is the picture of the reconstructed barrel.

Task 2 came later, from the Sarkisyan fitness measurements. It was not part of the Karpathy step.

The project conversation also began with the MATS eval guidelines and the repo scaffold. This file records the start of the task design, not a verbatim export of every earlier turn.
