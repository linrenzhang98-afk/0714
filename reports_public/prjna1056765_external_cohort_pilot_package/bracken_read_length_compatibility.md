# Bracken read-length compatibility

## Status

**BRACKEN_40NT_REDISTRIBUTION_ABSENT**

The hospital database contains redistribution files for 50, 75, 100, 150, 200, 250 and 300 nt. It does not contain a 40-nt file. Therefore the frozen 40-nt PRJCA039020 run `DRR770839` cannot proceed through Bracken with the existing database derivative.

The 50-nt redistribution is not a substitute for 40-nt reads. Option A may stop after Kraken2. Option B could later create an isolated 40-nt derivative, but this requires separate approval. Option C can use an external run only when its deposited read length is confirmed to match an installed redistribution exactly.

No redistribution was generated and no database was rebuilt or downloaded.
