This will store my attempt to produce and end-to-end solution for 
the VID/106 in a PCM system

Approach
1. Set up configuration in KSM
2. Use python to parse the xml task from KSM
3. Pull out the video modules, the placements of the video packets
4. Using that information, talk to GTS/DEC to decom the data and pull out the MPEG TS
   for all the video modules
5. Wrap the MPEG TS into a UDP packet and transmit so that players can playback on the Ethernet network