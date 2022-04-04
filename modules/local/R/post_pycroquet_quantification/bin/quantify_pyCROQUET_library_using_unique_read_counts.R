# Author: Victoria Offord
# Purpose: Annotate pyCROQUET library with pyCROQUET unique read counts

# Load dependencies -------------------------------------------------------

library(tidyverse)

# Command line arguments --------------------------------------------------

# Can't use argparse/optparse as they're not part of the Rocker tidyverse image
# Set trailingOnly to TRUE so we don't get all the Rscript args also
# Positional arguments: (1) library file (pyCROQUET format), (2) pyCROQUET unique read counts file (*.counts_counts.tsv.gz) and (3) sample name
args = commandArgs(trailingOnly = T)

if (length(args) != 3) {
  stop(paste0("Incorrect number of arguments (expecting 3):", length(args)))
}

# Library file ------------------------------------------------------------

# Assume that the library file is the first argument
library_file <- args[1]

# Check library file exists
if (!file.exists(library_file)) {
  stop(paste0("Library file does not exist:", library_file))
}

# Check library file is not empty
if (file.size(library_file) == 0L) {
  stop(paste0("Library file is empty:", library_file))
}

# Read in library file
library_data <- data.frame()
library_data <- tryCatch({
  # Read lines as we don't know how many header lines there will be
  tmp_lib <- readLines(library_file)
  # Get lines which start with ##
  header_lines_indices <- grep("^##", tmp_lib)
  if (length(header_lines_indices) == 0) {
    stop("There are no header lines in library file.")
  }
  header_lines <- tmp_lib[header_lines_indices]
  # Get all lines which don't include header lines
  tmp_lib <- tmp_lib[-header_lines_indices]
  # Check there are more than 1 lines in the library
  if (length(tmp_lib) <= 1) {
    stop("After removing headers, library is empty.")
  }
  # Check the first line starts with #id
  if (!grepl("#id", tmp_lib[1])) {
    stop("After removing headers, cannot find #id in header.")
  }
  # Replace #id with id
  tmp_lib[1] <- str_replace(tmp_lib[1], "#id", "id")
  # Convert to a data frame
  read.table(text = tmp_lib, sep = "\t", header = T) 
}, warning = function(w) {
  print(paste("Warning when reading library file: ", w))
}, error = function(e) {
  stop(paste("Error when reading library file: ", e))
})

# Double check library contains data
if (nrow(library_data) == 0) {
  stop("After processing, library_data contains no rows.")
}

# pyCROQUET counts --------------------------------------------------------

# Assume that the library file is the first argument
unique_read_count_file <- args[2]

# Check unique read count file exists
if (!file.exists(unique_read_count_file)) {
  stop(paste0("Unique read count file does not exist:", unique_read_count_file))
}

# Check unique read count file is not empty
if (file.size(unique_read_count_file) == 0L) {
  stop(paste0("Unique read count file is empty:", unique_read_count_file))
}

# Get sample name from arguments and check it's not null or empty
# Replace non-alphanumeric characters with underscores
sample_name <- character()
sample_name <- args[3]
if (length(sample_name) == 0) {
  stop("Sample name is empty.")
}
sample_name <- gsub("[[:space:]]+", "_", sample_name)

# Read in unique read count file
unique_read_counts <- data.frame()
unique_read_counts <- tryCatch({
  read.delim(unique_read_count_file, header = T, sep = "\t", skip = 2, col.names = c('QUERY', sample_name), check.names = F)
}, warning = function(w) {
  print(paste("Warning when reading library file: ", w))
}, error = function(e) {
  stop(paste("Error when reading library file: ", e))
})

# Check there are counts
if (nrow(unique_read_counts) == 0) {
  stop("After processing, unique_read_counts contains no rows.")
}

# Check overlap between sequences -----------------------------------------

# Make sure the column headers are as expected
# We don't have to check for the counts as we already set the header
if (sum(grepl('sgrna_seqs', colnames(library_data))) == 0) {
  stop('Library is missing sgrna_seqs in column headings')
}

# Before we join the library and counts, check that there are any matching sequences
overlapping_sequences <- vector()
overlapping_sequences <- intersect(library_data$sgrna_seqs, unique_read_counts$QUERY)
if (length(overlapping_sequences) == 0) {
  stop("There are no overlapping sequences.")
}

# Merge library and counts ------------------------------------------------

library_counts <- data.frame()
library_counts <- tryCatch({
  # Replace NA with 0 where sequence not found in counts
  # Rename id to #id
  library_data %>% 
    left_join(unique_read_counts, by = c('sgrna_seqs' = 'QUERY')) %>% 
    mutate(!!sample_name := ifelse(is.na(!!sym(sample_name)), 0, !!sym(sample_name))) %>%
    rename("#id" = "id")
}, warning = function(w) {
  print(paste("Warning when merging library with counts: ", w))
}, error = function(e) {
  stop(paste("Error when merging library with counts: ", e))
})

# Write counts to file ----------------------------------------------------

output_file <- str_replace(unique_read_count_file, 'query_counts.tsv.gz', 'query_to_library_counts.tsv')
tryCatch({
  write(header_lines, output_file)
  write.table(library_counts, output_file, row.names = F, sep = "\t", quote = F, append = T)
}, error = function(e) {
  stop(paste("Error when writing library counts: ", e))
})

# Check output file exists
if (!file.exists(output_file)) {
  stop(paste("Output file does not exist:", output_file))
}

# Check output file isn't empty 
if (file.size(output_file) == 0L) {
  stop(paste0("Output file is empty:", output_file))
}
