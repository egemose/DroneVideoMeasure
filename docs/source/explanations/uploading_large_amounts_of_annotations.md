# Uploading large amounts of annotations

2024-04-30: Currently the process of uploading large amounts of annotations uses excessive amounts of memory.

## Observations

There seems to be a data structure for undo and redo.
This can be found in the file static/video_annotator.js
around line 412 in the functions on_undo and on_redo.
Eash time the annotations are updated, the new state is
added to the `this.states` list.

If this is used for each individual annotation that is
added from the uploaded csv file, the memory consumption
will scale quadratically - O(n^2).

One approach for dealing with this is to avoid adding
states to `this.states` when uploading annotations
from a csv file.

Table with observations on number of annotations and memory usage:

| Annotations | Memory |
| ----------: | -----: |
| 0           | 120    |
| 1           | 772    |
| 2           | 2052   |
| 3           | 3956   |
| 4           | 6484   |
| 5           | 9640   |
| 6           | 13424  |
| 7           | 17832  |

## Solution

The implemented solution is to avoid saving the state on
the undo stack for each new annotation added from the
uploaded csv file.

This solutions have been implemented.
