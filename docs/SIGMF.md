# SigMF

The listener supports `.sigmf-meta` plus `.sigmf-data`, datatypes `cf32_le` and `ci16_le`, capture frequency, sample rate, aligned file size, offsets, lengths, and chunked memory-mapped reads. Authentic mode additionally needs a provenance manifest with source, observatory, capture timestamp, license/terms, file size, and SHA-256. Large IQ files are never committed.
