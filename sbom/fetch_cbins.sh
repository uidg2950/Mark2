#!/bin/bash
#=======================================================================#
# This batch script detects the source code folder of each 'component'  #
# and their related generated binaries obtained after compile them      #
# individualy within the docker environment provided in context of      #
# technical project setup.                                              #
# Here must be mentioned that the make scripts of the project from      #
# various components are not properly implemented therefore by          #
# invokation of make commands for some of them, therefore the thrown    #
# errors will lead to incomplete or failed clean-up and or compile and  #
# linking processes so that data collection will not be completed.      #
# Currently the used strategy is to execute only make clean/clobber/    #
# uninstall commands without invoking make-component to generate the    #
# binaries, and compare the entire source code folder agains a copy of  #
# it which plays the role of a reference duplicate!                     #
#-----------------------------------------------------------------------#
# Language: Unix/Linux Shell Script. Tested on Conti Ubuntu.            #
# Author: Dr. Eugen Victor Cuteanu                                      #
# Department: A AN PL2 RD EMEA RBG SW APP2                              #
# Date & Time: 11-06-2024 , 11:40pm Germany.                            #
# Version: 0.1 draft / prototype.                                       #
# Copyright: Continental Automotive AG                                  #
#=======================================================================#

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# Currently jsut call:
#    ./fetch_cbins.sh [FOLDER_WORKAREA] [FOLDER_SRC] [FOLDER_REF] [FILE_TARGET] [MODE]
#    All parameters must be in the same order as above, and those unspecified will be set to default values.
# having this script within the main folder of the workarea ! 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 


# Capturing some infrastructure parameters:
SCRIPT_NAME=$(basename "${0}")
FOLDER_NAME=$(dirname "${0}")
CURDIR_NAME=$(pwd)

# List the current folder setup:
echo "Script name: "$SCRIPT_NAME
echo "Folder name: "$FOLDER_NAME
echo "Current dir: "$CURDIR_NAME
# Initialize some local variables tracking folder options
folder_work=""
folder_src=""
folder_ref=""
folder_trg=""
folder_mode=0

# Define the function
subtract_folders() {
    local folder_src=$1   # Source folder
    local folder_work=$2  # Working folder
    # Remove the common prefix (folder_work) from folder_src
    local relative_folder=${folder_src#$folder_work}
    # Add "./" to the beginning of the relative folder if it doesn't start with "/" or "./"
    if [[ ! $relative_folder =~ ^/ && ! $relative_folder =~ ^\.\/ ]]; then
        relative_folder="./$relative_folder"
    elif [[ $relative_folder =~ ^/ ]]; then
        relative_folder=".$relative_folder"
    fi
    # Print the relative folder path
    echo "$relative_folder"
}

# Function for reformating folder to full length path string.
normalize_folder() {
    local folder=$1  # Get the folder string as argument
    # Check if folder starts with "./"
    if [[ "$folder" == "." || "$folder" == "./" ]]; then
        folder="$(realpath .)"
    fi
    if [[ $folder == "./"* ]]; then
        folder=$CURDIR_NAME"/""${folder#"./"}"
    # Check if folder starts with "/"
    elif [[ $folder == "/"* ]]; then
        folder=$folder"";
    # If folder starts with neither "./" nor "/", handle accordingly
    else
        folder=$CURDIR_NAME$folder
    fi
    # Print the normalized folder path
    echo "$folder"
}

# Check if the script is called with an argument
# Option 0 is enough
if [ $# -eq 5 ]; then
    folder_work=$(normalize_folder $1)
    cd $folder_work
    folder_src=$(normalize_folder $2)
    folder_ref=$(normalize_folder $3)
    folder_trg=$(normalize_folder $4)
    folder_mode=$5
elif [ $# -eq 4 ]; then
    folder_work=$(normalize_folder $1)
    cd $folder_work
    folder_src=$(normalize_folder $2)
    folder_ref=$(normalize_folder $3)
    folder_trg=$(normalize_folder $4)
    folder_mode=2
elif [ $# -eq 3 ]; then
    folder_work=$(normalize_folder $1)
    cd $folder_work
    folder_src=$(normalize_folder $2)
    folder_ref=$(normalize_folder $3)
    folder_trg=$folder_work"/.build/packages-target";
    folder_mode=2
elif [ $# -eq 2 ]; then
    folder_work=$(normalize_folder $1)
    cd $folder_work
    folder_src=$(normalize_folder $2)
    folder_ref=$folder_work"/refsource";
    folder_trg=$folder_work"/.build/packages-target";
    folder_mode=2
elif [ $# -eq 1 ]; then
    folder_work=$(normalize_folder $1)
    cd $folder_work
    folder_src=$folder_work"/package";
    folder_ref=$folder_work"/refsource";
    folder_trg=$folder_work"/.build/packages-target";
    folder_mode=2
elif [ $# -eq 0 ]; then
    echo "No parameter given, therefore all implicit settings will be applied"
    folder_work=$(normalize_folder "./")
    cd $folder_work
    folder_src=$folder_work"/package";
    folder_ref=$folder_work"/refsource";
    folder_trg=$folder_work"/.build/packages-target";
    folder_mode=2
elif [ $# -ge 6 ]; then
    echo "Invalid number of arguments! Exit."
    exit 1
fi


# print the current setup folder after preprocessing.
echo "Using:"
echo "Workarea folder:"$folder_work
echo "Sourcode folder:"$folder_src
echo "Reference folder:"$folder_ref
echo "Target folder:"$folder_trg
echo "Work mode:"$folder_mode

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

## File verification
[[ ! -f "${folder_trg}" ]] && echo "Error: ${folder_trg} doesn't exist" && exit 1

## Reading the list of package names.
IFS=' ' read -r -a packages_target <<< "$(cat ${folder_trg})"

packages_path=()
## Listing Target packages in packages-target file
for pckg in ${packages_target[@]}; do
    basename=$(echo ${pckg}| awk -v FS='--' '{print $1}')
    packages_path+=( "${basename}" )
done

## Count of Packages & Path-end names.
trg_elements=${#packages_target[@]}

## Listing Target packages in packages-target file
#for pckg in ${packages_target[@]}; do
#    echo $pckg
#done

# packages to be excluded
# This list comes from layers/project/sa515m/config/package file.
# This is not really needed by Conmod Project
distclean_packages=( conti-fc-nav-hal-sepolicy conti-tp-hal-sepolicy )

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# Function to truncate directory path based on deepness threshold
truncate_directory_path() {
    local directory_path="$1"
    local deeplim="$2"
    # Count the number of "/" characters in the directory path
    local num_slashes=$(awk -F'/' '{print NF-1}' <<< "$directory_path")
    # Check if tlibxml-parser-perlhe number of slashes exceeds the threshold
    if [ "$num_slashes" -gt "$deeplim" ]; then
        # Truncate the directory path
        truncated_path=$(awk -F'/' -v lim="$deeplim" 'BEGIN{OFS=FS} {for (i=1; i<=lim+1; i++) printf "%s%s", $i, (i<=lim) ? "/" : ""}' <<< "$directory_path")
        echo "$truncated_path"
    else
        # No truncation needed
        echo "$directory_path"
    fi
}


# Function to process the file and extract unique directory paths within a specified scope folder!
process_reports_files_paths() {
    local input_file="$1"
    local scope_path="$2"
    local output_file="$3"
    local paths=()
    local deeplim=3;
    # tuning the deepness offset!
    main_depth=$(awk -F'/' '{print NF-1}' <<< "$CURDIR_NAME")
    ((deeplim+=$main_depth))
    # Check if the input file exists
    if [ ! -f "$input_file" ]; then
        echo "Error: Input file '$input_file' not found."
        return 1
    fi
    # Read the input file line by line
    while IFS= read -r line; do
        # Check if the line starts with the specified scope path
        if [[ "$line" == "$scope_path"* ]]; then
            # Extract directory path (remove filename)
            directory_path="${line%/*}"
            # ensure limited deepness, to avoid unnecessary computing
            truncated_path=$(truncate_directory_path "$directory_path" "$deeplim")
            # Append the directory path to the array
            paths+=("$truncated_path")
        fi
    done < "$input_file"
    # Sort and remove duplicates from the array
    unique_paths=($(printf "%s\n" "${paths[@]}" | sort -u))
    # Save the unique paths to the output file
    printf "%s\n" "${unique_paths[@]}" > "$output_file"
}


# Function to sort folder strings by depth (number of "/") and eliminate subdirectories
sort_and_eliminate_subdirs_from_file() {
    local filename=$1
    local folder_array=()
    local continue_processing=true
    local MINDEEP=3;
    # callibrating the deepness offset!
    main_depth=$(awk -F'/' '{print NF-1}' <<< "$CURDIR_NAME")
    ((MINDEEP+=$main_depth))
    # Read all lines from the file into an array
    while IFS= read -r line; do
        folder_array+=("$line")
    done < "$filename"
    # Sort the array alphabetically and remove duplicates
    IFS=$'\n' sorted_folders=($(sort -u <<<"${folder_array[*]}"))
    # principal loop, ensuring that all cases will be considered and processed.
    while $continue_processing; do
        continue_processing=false
        # Iterate through the sorted array
        for ((i = 0; i < ${#sorted_folders[@]}; i++)); do
            current_folder="${sorted_folders[i]}"
            # bypass the blank lines!
            if [ ${#current_folder} -eq 0 ]; then
                continue;
            else
                blank=0;
                # DEBUG: echo $i >&2
            fi
            # retrieve deepness value aka number of imbricated subfolders.
            depth=$(tr -dc '/' <<< "$current_folder" | wc -c)
            # DBG: echo "Processing dir: "$current_folder >&2
            # Check if depth is smaller than MINDEEP
            if ((depth < MINDEEP)); then
                sorted_folders[i]='';  # Set current folder to empty
                continue  # Skip to the next iteration
            fi
            # Check against following lines
            for ((j = i + 1; j < ${#sorted_folders[@]}; j++)); do
                next_folder="${sorted_folders[j]}"
                if [[ $next_folder == $current_folder* ]]; then
                    sorted_folders[j]=''  # Cancel the next line
                    continue_processing=true
                fi
            done
        done
        # Remove empty entries
        non_empty_folders=()
        for folder in "${sorted_folders[@]}"; do
            if [[ -n $folder ]]; then
                non_empty_folders+=("$folder")
            fi
        done
        # Sort the array again
        sorted_folders=($(sort <<<"${non_empty_folders[*]}"))
    done
    # Print the resulting array
    # printf "%s\n" "${sorted_folders[@]}"
    echo "${sorted_folders[@]}"
}


# function for dumping an string array into a file.
write_sorted_folders_to_file() {
    local filename="$1"
    local sorted_folders=( ${@:2} )
    local num_lines=0
    # check if the file do exist, case when warning message will be listed.
    if [ -f "$filename" ]; then
        echo "Warning: File '$filename' already exists. Contents will be appended." >&2
    fi
    # Loop to write sorted_folders to the file
    for folder in "${sorted_folders[@]}"; do
        folder=$(echo "$folder" | tr -d '[:space:]')
        echo "$folder" >> "$filename"
        num_lines=$((num_lines + 1))
    done
    # Create an empty file if no lines were written
    if [ "$num_lines" -eq 0 ]; then
        touch "$filename"
    fi
    # Return the number of lines written
    echo "$num_lines"
    # ALTERNATIVE: echo "${#sorted_folders[@]}"
}


# Function to find the nearest common branch among directories containing a specific file
find_nearest_common_branch() {
    local current_path="$1"
    local file_name_regex="$2"
    # Find all directories containing the specific file
    local directories_with_file=()
    while IFS= read -r directory; do
        directories_with_file+=("$directory")
    done < <(find "$current_path" -type f -regex "$file_name_regex" -exec dirname {} \;)
    # Find the common branch among the directories
    local common_branch=""
    for directory in "${directories_with_file[@]}"; do
        if [[ -z "$common_branch" ]]; then
            common_branch="$directory"
        else
            common_branch=$(printf "%s\n%s" "$common_branch" "$directory" | sed -e 'N;s/^\(.*\).*\n\1.*$/\1/')
        fi
    done
    # Return the nearest common branch
    echo "$common_branch"
}


# this function ensures that no unnecesary duplicates are subdirectories are added to the list.
append_common_path() {
    local selected_paths="$1"
    local common_path="$2"
    # Split selected_paths into an array using semicolon as delimiter
    IFS=';' read -ra paths_array <<< "$selected_paths"
    # local flag variable
    local found_common=false
    # Iterate over each path in the array
    for path in "${paths_array[@]}"; do
        # Check if common_path is the common part of the current path
        if [[ "$path" == *"$common_path"* ]]; then
            found_common=true
            break
        fi
    done
    # If common_path is not the common part of any path, append it to selected_paths
    if ! $found_common; then
        # Append common_path with semicolon delimiter if selected_paths is not empty
        if [ -n "$selected_paths" ]; then
            selected_paths+=";"
        fi
        selected_paths+="$common_path"
    fi
    # provide the result
    echo "$selected_paths"
}


# This function searches for those folders which contains either within or its subfolders both source files and make files.
filter_paths() {
    local report_path=$1
    local scope_path=$2
    local selected_paths=""
    local current_path
    local crt_depth
    local MINDEEP=3;
    # adust the folder deepness constant.
    main_depth=$(awk -F'/' '{print NF-1}' <<< "$CURDIR_NAME")
    ((MINDEEP+=$main_depth))
    # DBG: echo "Reference deepness: "$MINDEEP >&2
    # Read each line from the file
    while IFS= read -r line; do
        # Check if string path points to a file
        if [[ -f "$line" ]]; then
            current_path=$(dirname "$line")
        else
            current_path="$line"
        fi
        # absolutize the path
        if [[ $current_path == "./"* ]]; then
            current_path="$CURDIR_NAME/${current_path#./}"
        fi
        # check if it is in the specified scope
        if [[ $current_path == $scope_path* ]]; then
            # DEBUG:
            # echo $current_path >&2
            # Loop until reaching scope directory or a match is found
            while [[ "$current_path" != $scope_path ]]; do
                # Find the minimum subpath containing either Makefile or CMake*.*
                # subpathA=$(find "$current_path" \( -name "Makefile" -o -name "CMake*.*" \) -print -quit 2>/dev/null)
                # subpathA=$(find "$current_path" -regex '.*\(Makefile\|CMake.*\)' -print -quit 2>/dev/null)
                subpathA=$(find_nearest_common_branch "$current_path" ".*\(Makefile\|CMake.*\)")
                # subpathB=$(find "$current_path" \( -name "*.c*" -o -name "*.h*" \) -print -quit 2>/dev/null)
                # subpathB=$(find "$current_path" -regex '.*\.\(c\|cpp\|h\|hpp\)$' -print -quit 2>/dev/null)
                subpathB=$(find_nearest_common_branch "$current_path" ".*\.\(c\|cpp\|h\|hpp\)$")
                # check if some non void result obtained:
                if [[ -n $subpathA && -n $subpathB ]]; then
                    # Extract the directory part of the subpath
                    # subpathA=$(dirname "$subpathA")
                    # subpathB=$(dirname "$subpathB")
                    # Initialize variables
                    common_path=""
                    # Split the paths into arrays using the '/' delimiter
                    IFS='/' read -ra pathA <<< "$subpathA"
                    IFS='/' read -ra pathB <<< "$subpathB"
                    # Iterate through each folder level
                    for ((i=0; i<${#pathA[@]} && i<${#pathB[@]}; i++)); do
                        # Check if folder names at the current level match
                        if [[ "${pathA[i]}" == "${pathB[i]}" ]]; then
                            # Append the matching folder name to the common path
                            common_path+="/${pathA[i]}"
                        else
                            # Stop iteration when a mismatch is found
                            break
                        fi
                    done
                    # Print the common path DEBUG: echo "Common path: $common_path" >&2
                    # Append the subpath to the selected paths
                    if [[ -z $selected_paths ]]; then
                        selected_paths="$common_path"
                    else
                        # selected_paths+=";$common_path"
                        result=$(append_common_path "$selected_paths" "$common_path")
                        selected_paths=$result;
                    fi
                    break  # Exit the loop if a match is found
                fi
                # Remove the last subfolder from the current path
                current_path=$(dirname "$current_path")
                # in case of too short deepness then abort the cycle.
                crt_depth=$(awk -F'/' '{print NF-1}' <<< "$current_path")
                # echo "Actual deepness: "$crt_depth >&2
                if ((crt_depth < MINDEEP)); then
                    break;
                fi
            done
            crt_depth=$(awk -F'/' '{print NF-1}' <<< "$current_path")
            # echo "Actual deepness: "$crt_depth >&2
            if ((crt_depth < MINDEEP)); then
                break;
            fi
        fi
    done < "$report_path"
    # Print the selected paths
    # echo $selected_paths >&2
    echo "$selected_paths"
}


# Function to read file paths, check if they are executables or shared libraries, and return their names
# Only considers lines starting with the specified string
# The third argument determines the method for checking file type: 'file' or 'mime'
check_executables() {
    local file_path=$1
    local start_string=$2
    local method=$3
    local executable_files=()

    # Check if the file exists
    if [ -f "$file_path" ]; then
        # Read each line from the file
        while IFS= read -r line; do
            # Check if the line starts with the specified string
            if [[ $line == "$start_string"* ]]; then
                if [ -x "$line" ]; then
                    if [ "$method" == "file" ]; then
                        # Use 'file' command to determine file type
                        if file "$line" | grep -qE "ELF.*executable|ELF.*shared object"; then
                            # Extract the file name without path and add it to the array
                            file_name=$(basename "$line")
                            executable_files+=("$file_name")
                        fi
                    elif [ "$method" == "mime" ]; then
                        # Use 'file --mime-type --brief' to get the MIME type of the file
                        mime_type=$(file --mime-type --brief "$line")
                        # Check if the MIME type indicates an executable or shared library
                        if [[ $mime_type == application/x-executable* || $mime_type == application/x-sharedlib* ]]; then
                            # Extract the file name without path and add it to the array
                            file_name=$(basename "$line")
                            executable_files+=("$file_name")
                        fi
                    else
                        echo "Error: Invalid method specified. Please choose 'file' or 'mime'."
                        return 1
                    fi
                fi
            fi
        done < "$file_path"
    else
        echo "Error: File $file_path not found."
        return 1
    fi
    # Return the array of executable file names
    echo "${executable_files[@]}"
}



# function for copying missing files from a reference folder to the current one
copy_files_and_list() {
    local source_dir=$1
    local dest_dir=$2
    local mode=$3
    local list_files=()
    local num_copied=0
    # check if directory is there available.
    if [ ! -d "$source_dir" ]; then
        echo "Source directory does not exist"
        return
    fi
    # check if this directory is there available.
    if [ ! -d "$dest_dir" ]; then
        echo "Destination directory does not exist"
        return
    fi
    # Find all files in source_dir that do not exist in dest_dir
    while IFS= read -r -d '' src_file; do
        # Get the relative path of the source file
        rel_path="${src_file#$source_dir/}"
        dest_file="$dest_dir/$rel_path"
        # Check if the destination file exists
        if [ ! -e "$dest_file" ]; then
            # Create the destination directory if it doesn't exist
            mkdir -p "$(dirname "$dest_file")"
            # Copy the file
            cp "$src_file" "$dest_file"
            ((num_copied++))
            # Collect file names or paths based on the mode
            if [[ "$mode" -eq 1 ]]; then
                list_files+="$(basename "$src_file")"
            elif [[ "$mode" -eq 2 ]]; then
                list_files+=("$src_file")
            fi
        fi
    # closing loop while feeded with data.
    done < <(find "$source_dir" -type f -print0)
    # Return results based on the mode
    if [[ "$mode" -eq 1 || "$mode" -eq 2 ]]; then
        echo "${list_files[@]}"
    else
        echo "$count"
    fi
}


# function for load data from file
read_folder_strings_from_file() {
    local filename="$1"
    local -a folder_strings=()
    # Constants
    EMPTY_RETURN="n/a"
    FILE_NOT_FOUND_RETURN="unknown"
    # Check if the file exists
    if [ ! -f "$filename" ]; then
        echo "$FILE_NOT_FOUND_RETURN"
        return
    fi
    # Read the file line by line
    while IFS= read -r line; do
        # Check if the line is not empty
        if [ -n "$line" ]; then
            folder_strings+=("$line")
        fi
    done < "$filename"
    # Check if the array is empty
    if [ ${#folder_strings[@]} -eq 0 ]; then
        echo "$EMPTY_RETURN"
    else
        # Return the array
        echo "${folder_strings[@]}"
    fi
}


# function for line separator string generation
repeat_string_printf() {
    local str="$1"
    local num_repeats="$2"
    printf "%0.s$str" $(seq 1 $num_repeats)
}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Generate date in the format dd-mm-yyyy
date=$(date +"%d-%m-%Y")
# Generate time in the format hh:mm:ss
time=$(date +"%T")
# Generate UUID  # uuid=$(uuidgen)
uuid=$(cat /proc/sys/kernel/random/uuid)
# Construct JSON string
json_string="\"stamp\": { \"date\": \"$date\", \"time\": \"$time\", \"uuid\": \"$uuid\" }"
json_header=' { "name": "Victorian Folder Database.", "version": "0.1", "owner": "FOSS", "components": [ ';
json_footer=' ], '$json_string' }';

json_entire=$json_header;
# delete all previusly generated report files!
rm -f binscan_*.*

relfolder_src=$(subtract_folders "$folder_src" "$folder_work")

# For each listed package:
for (( i=0;i<$trg_elements;i++ )); do
    echo '';
    printf "Progress: %.2f%%\n" "$(bc -l <<< "scale=2; $i * 100 / $trg_elements")";
    echo "Operating with: ""${packages_target[i]}"
    # check non-exclusion
    if [[ ! "${distclean_packages[*]}" =~ "${packages_target[i]}" ]]; then
        comp_name=${packages_target[i]};
        # Check if the input string contains the sequence "--"
        if [[ $comp_name == *"--"* ]]; then
            # Remove "--" and the rest of the right side substring
            base_name=${comp_name%%--*}
        else
            base_name=$comp_name;
        fi

        # DEBUG selector:
        #if [[ $base_name != "attr" ]]; then
        #    continue;
        #fi

        # define file name:
        reportname="binscan_"${comp_name}".log";
        # clean the component binaries:
        make $comp_name-clean CAS_TARGET_HW=sa515m J=1
        make $comp_name-clobber CAS_TARGET_HW=sa515m J=1
        make $comp_name-uninstall CAS_TARGET_HW=sa515m J=1
        # find "$folder_path" -type f \( -name "*.so" -o -name "*.so.*" \) | grep -P "\.so(\.[0-9]+)?$" | xargs rm -f

        # check computing mode - here by 'negation' i.e. detect missing files after clean-up compared to a reference folder.
        if [[ $folder_mode == 1 ]]; then
            # timing
            sleep 2
            datetimeref=$(date -d '1 second ago' +'%Y-%m-%d %H:%M:%S')
            echo "Time after delay is: ""$datetimeref"
            # perform the effective compilation and binaries installations.
            make $comp_name CAS_TARGET_HW=sa515m J=1
            # search for latest modified file i.e. those opereated on.
            find "$folder_work" -type f -newermt "${datetimeref}" > "${reportname}"

            # handling the reports
            sort "${reportname}" | uniq > "${reportname}"".unique"
            mv "${reportname}.unique" "${reportname}"
            # preliminary processing: extract paths and remove file names!
            process_reports_files_paths "${reportname}" "${folder_src}" "${reportname}_once"
            # intermediate processing: need single line for each folder string!
            sorted_and_unique_folders=($(sort_and_eliminate_subdirs_from_file "${reportname}_once"))
            # dump data to file.
            num_lines_written=$(write_sorted_folders_to_file "${reportname}_reduced" "${sorted_and_unique_folders[@]}")
            echo "Number of lines written: $num_lines_written"
            # Print the result
            printf "Sorted unique: %s\n" "${sorted_and_unique_folders[@]}"
            # Apply special selection algorithm, so that only relevant entries will be kept.
            filtered_paths=$(filter_paths "${reportname}_reduced" "$folder_src")
            # Echo found strings:
            echo "- - - - - >> ""Filtered: "$filtered_paths
            # scan for binaries.
            execs=$(check_executables "${reportname}" "${folder_src}" "mime")
            echo "- - - - - >> ""Executables: "${execs[@]}
            # conversion to string.
            IFS=';' execs_str="${execs[*]}"
            # create a new json entry for the current component.
            json_entry='{ "base":"'$base_name'", "name":"'$comp_name'", "paths":"'$filtered_paths'", "execs":"'$execs_str'" }';

        # check computing mode - here by compiling the component and detect produced content i.e. positive method.
        elif [[ $folder_mode == 2 ]]; then

            # execute transfer of missing file back from reference to current sourcode subfolder.
            retstr=$(copy_files_and_list "$folder_ref" "$folder_src" "$folder_mode")
            IFS=' ' read -r -a file_list <<< "$retstr"
            # populate content to a log file.
            num_lines_written=$(write_sorted_folders_to_file "${reportname}_found" "${file_list[@]}")
            echo "Number of lines written: $num_lines_written"
            # just pick up unicates elements.
            sort "${reportname}_found" | uniq > "${reportname}"".unique"
            mv "${reportname}.unique" "${reportname}_detect"
            # as only folder path string are required, remove unnecesary content-
            process_reports_files_paths "${reportname}_detect" "${folder_ref}" "${reportname}_once"
            # logged content needed in RAM as well.
            detected_paths=$(read_folder_strings_from_file "${reportname}_once")
            # Echo found paths:
            echo "- - - - - >> ""Filtered: "$detected_paths
            # scan for binaries.
            execs=$(check_executables "${reportname}_detect" "${folder_ref}" "mime")
            echo "- - - - - >> ""Executables: "${execs[@]} 
            # message separator.
            echo $(repeat_string_printf "-" 80)        
            # conversion to string.
            IFS=';' execs_str="${execs[*]}"
            # create a new json entry for the current component.
            json_entry='{ "base":"'$base_name'", "name":"'$comp_name'", "paths":"'$detected_paths'", "execs":"'$execs_str'" }';

        # otherwise just message nonsense.  
        else
            echo "boom"
        fi
      
        # check if separator must be inserted.
        if [ "$i" -gt 0 ]; then
            json_entry=', '$json_entry;
        fi
        # append a new entry to the main json string.
        json_entire+=$json_entry;

    fi
done

# add terminator signature.
json_entire+=$json_footer;

# dump json string to a file.
echo "$json_entire" > folders.json

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

