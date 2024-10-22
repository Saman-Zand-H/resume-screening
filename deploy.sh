#!/bin/bash

set -e

BRANCH_DEV="dev"
BRANCH_STAGE="stage"
BRANCH_MASTER="master"
PREFIX_STAGE="stage-"
DEFAULT_VERSION="0.0.0"

get_latest_tag() {
    local branch=$1

    git fetch --tags

    if [[ "$branch" == "$BRANCH_STAGE" ]]; then
        git tag -l "$PREFIX_STAGE*" --sort=-v:refname | head -n 1 || echo "${PREFIX_STAGE}${DEFAULT_VERSION}"
    elif [[ "$branch" == "$BRANCH_MASTER" ]]; then
        git tag -l "$PREFIX_STAGE*" --sort=-v:refname | head -n 1 | sed "s/$PREFIX_STAGE//" || echo "$DEFAULT_VERSION"
    else
        echo "$DEFAULT_VERSION"
    fi
}

increment_version() {
    local version=$1
    local part=$2
    IFS='.' read -r major minor patch <<<"$version"

    case "$part" in
    major)
        ((major++))
        minor=0
        patch=0
        ;;
    minor)
        ((minor++))
        patch=0
        ;;
    patch)
        ((patch++))
        ;;
    *)
        echo "Invalid version part: $part"
        exit 1
        ;;
    esac
    echo "$major.$minor.$patch"
}

merge_tag_push() {
    local source_branch=$1
    local target_branch=$2
    local tag=$3

    local current_branch
    current_branch=$(git rev-parse --abbrev-ref HEAD)

    echo "Switching to $target_branch for merge..."
    git checkout "$target_branch"

    echo "Pulling latest changes for $source_branch..."
    git pull origin "$source_branch"

    echo "Merge $source_branch into $target_branch with tag $tag"
    git merge --no-ff "$source_branch" -m "Merge $source_branch into $target_branch with tag $tag"

    echo "Tagging with $tag..."
    git tag "$tag"

    echo "Pushing $target_branch and tag $tag..."
    git push origin "$target_branch"
    git push origin "$tag"

    echo "Switching back to $current_branch..."
    git checkout "$current_branch"
}

echo "Select action: [stage, production]"
read -r action

if [[ "$action" == "stage" ]]; then
    source_branch=$BRANCH_DEV
    target_branch=$BRANCH_STAGE

    echo "Fetching latest stage tag..."
    latest_tag=$(get_latest_tag "$target_branch")
    echo "Latest stage tag: $latest_tag"

    echo "Select version increment: [major, minor, patch]"
    read -r increment

    new_version=$(increment_version "$latest_tag" "$increment")
    tag="${new_version}"
elif [[ "$action" == "production" ]]; then
    source_branch=$BRANCH_STAGE
    target_branch=$BRANCH_MASTER

    echo "Fetching latest stage tag..."
    latest_tag=$(get_latest_tag "$BRANCH_STAGE")
    tag="${latest_tag//$PREFIX_STAGE/}"
    echo "Latest production tag to be used: $tag"
else
    echo "Invalid action: $action"
    exit 1
fi

echo "====================================="
echo "Deployment Summary:"
echo "-------------------------------------"
echo "Source branch        : $source_branch"
echo "Target branch        : $target_branch"
echo "Latest tag           : $latest_tag"
echo "Version to be used   : $tag"
echo "-------------------------------------"
echo "Changes will be pushed to:"
echo "  - Branch: $target_branch"
echo "  - Tag: $tag"
echo "====================================="

echo "Do you want to proceed with the push? [yes/no]"
read -r confirmation

if [[ "$confirmation" == "yes" ]]; then
    merge_tag_push "$source_branch" "$target_branch" "$tag"
    echo "Deployment completed successfully!"
else
    echo "Deployment aborted by the user."
fi
