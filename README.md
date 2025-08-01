# Precompute ROS Reference

## Overview

This repository provides a GitHub action and utilities to precompute a reference of all ROS2 packages in a given project and of the nodes, launch files and interfaces they provide. Then the reference is meant to be included in a documentation of the project. The action [Sphinx-Build](https://github.com/hawaitech/sphinx-build.git) can be used to create such a documentation.

## Usage

This action dowloads is executable in `${src-path}/tmp` and executes it to produce a reference of all ROS2 packages in `${src-path}`. This reference is stored in `${src-path}/tmp/precomputed_docs`. The execubles are stored in `${src-path}/tmp/precompute-ros-reference`.

```yaml
- name: Reference and introspect ROS executables
  uses: https://github.com/hawaitech/precompute-ros-reference.git@feature/precompute_IO_graphs
  with:
    src-path: /workspace/src
    graph-style: /workspace/src/docs/source/ros2-graph_style.yaml
```

### Include the action in your worklow

The workflow below illustrates the usage with the [Sphinx-Build](https://github.com/hawaitech/sphinx-build.git) action. The global process is :

1. We assume that the ROS2 environment and packages are already built in a previous job `build`.
2. Precompute the reference of the ROS2 packages.
    a. In a local execution, the reference is copied to the host machine in the directory `src/tmp/precomputed_docs`.
    b. In a remote execution, the reference is stored as an artifact.
3. Build the documentation using the [Sphinx-Build](https://github.com/hawaitech/sphinx-build.git)
    a. In a local execution, the reference is copied from the host machine to the container.
    b. In a remote execution, the reference is downloaded from the artifact.
    c. When building the documentation, the reference can be accessed in the `docs/source/precomputed` directory.

```yaml
precompute_doc:
    runs-on: my_server # The host on which you want to execute this
    needs: build # This requires to build the ROS2 environment and packages before
    container:
      image: my_image # The image with your built environment
      volumes:
        - /var/www/html:/data # Only used for local execution, remote execution relies on artifacts
    steps:
      - name: Clean & recreate precompute docs directory
        run: |
          rm -rf /workspace/src/tmp/precomputed_docs
          sudo mkdir -p /workspace/src/tmp/precomputed_docs
          sudo chown -R mydocker_host:my_docker_user /workspace/src/tmp/precomputed_docs
      - name: Reference and introspect ROS executables
        uses: https://github.com/hawaitech/precompute-ros-reference.git@feature/precompute_IO_graphs
        with:
          src-path: /workspace/src
          graph-style: /workspace/src/docs/source/ros2-graph_style.yaml
      - name: Upload precomputed doc
        if: ${{ ! env.ACT_SKIP_CHECKOUT }}
        uses: actions/upload-artifact@v3
        with:
          name: precomputed_docs
          path: /workspace/src/tmp/precomputed_docs
      - name: Copy precomputed doc if local
        if: ${{ env.ACT_SKIP_CHECKOUT }}
        run: |
          rm -rf /data/src/precomputed
          sudo mkdir -p /data/precomputed
          sudo chown -R ubuntu:ubuntu /data/precomputed
          sudo cp -r /workspace/src/tmp/precomputed_docs/. /data/precomputed
build-html:
    needs: precompute_doc
    runs-on: my_doc_server # The host on which you want to execute this, might be different from the one used to precompute the doc
    container:
      image: my_doc_builder image # The image to produce doc, does not require the built environment
      volumes:
        - /var/www/html:/data
    steps:
      - name: checkout
        uses: actions/checkout@v4
      - name: Download precomputed docs
        if: ${{ ! env.ACT_SKIP_CHECKOUT }}
        uses: actions/download-artifact@v3
        with:
          name: precomputed_docs
          path: docs/source/precomputed
      - name: Move precomputed doc if local
        if: ${{ env.ACT_SKIP_CHECKOUT }}
        run: |
          sudo cp -r /data/precomputed docs/source/precomputed
      - name: Sphinx Build
        uses: https://github.com/hawaitech/sphinx-build.git@release/v3
        with:
          build-root: /data
```

### Include precomputed reference in your documentation

When building the documentation, the reference can be accessed in the `docs/source/precomputed` directory. So you can include refer to it from the .rst files of documenation. For example, in file located in `docs/source`, you can include the ROS2 node graph of a package with the command below:

```rst
.. mermaid:: ./precomputed/my_package/my_node/io_graph.md
    :caption: Node interfaces
```

## Provided features

### Mermaid graph of ROS2 nodes' interfaces

```rst
.. mermaid:: ./precomputed/my_package/my_node/io_graph.md
    :caption: Node interfaces
```

Usage of mermaid graphs requires the dependency `sphinxcontrib-mermaid` to be declared in your `docs/source/conf.py` and `docs/source/requirements.txt`.

**NB : Mermaid graph are currently not correctly supported by Firefox. Please use Chromium or other browsers instead.**

The style of the graph can be configured by providing a yaml file to the action. The sugggested style is defined in `doc/ros2-graph_style.yaml`. For more details, visit <https://github.com/kiwicampus/ros2_graph>.
