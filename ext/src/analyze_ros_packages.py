"""Analyze all ROS executables in a folder."""

import argparse
import os
import shutil
from pathlib import Path

from defusedxml import ElementTree
from launch import LaunchDescription, LaunchService
from launch.actions import ExecuteProcess, RegisterEventHandler, Shutdown, TimerAction
from launch.event_handlers import OnProcessStart
from launch_ros.actions import Node
from ros2_graph import __main__ as ros2_graph
from ros2pkg.api import get_executable_paths


def find_ros_packages(folder_path: str) -> list[str]:
    """Find name of ROS packages in a folder."""
    ros_packages = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file == "package.xml":
                package_xml_path = Path(root) / file
                try:
                    tree = ElementTree.parse(package_xml_path)
                    root_element = tree.getroot()
                    package_name = root_element.find("name").text
                    ros_packages.append(package_name)
                except ElementTree.ParseError:
                    print(f"Error parsing {package_xml_path}")
                except AttributeError:
                    print(f"Package name not found in {package_xml_path}")
    return ros_packages


def get_ros_executables(pkg_name: str) -> list[str]:
    """Get list of executables in a ROS package."""
    path_list = get_executable_paths(package_name=pkg_name)
    return [Path(path).name for path in path_list]


def generate_launch_analysis_description(
    pkg_name: str,
    exec_name: str,
    doc_path: Path,
    style_path: Path,
    max_duration: float,
) -> LaunchDescription:
    """Generate a launch description for to analyze a single ROS executable."""
    node_name = exec_name.replace(".py", "_py")
    ros2_graph_cmd = [
        "python3",
        "-c",
        "from ros2_graph import __main__ as ros2_graph; ros2_graph.main()",
        "/" + node_name,
        "-o",
        str(doc_path / "io_graph"),
    ]
    if style_path.exists():
        ros2_graph_cmd += ["--styleConfig", str(style_path)]
    node_under_test = Node(package=pkg_name, executable=exec_name, name=node_name)
    return LaunchDescription(
        [
            node_under_test,
            RegisterEventHandler(
                OnProcessStart(
                    target_action=node_under_test,
                    on_start=[
                        ExecuteProcess(
                            cmd=ros2_graph_cmd,
                            output="screen",
                            on_exit=[Shutdown()],
                        )
                    ],
                )
            ),
            TimerAction(period=max_duration, actions=[Shutdown()]),
        ]
    )


def post_process_mermaid_md(doc_path: Path) -> None:
    """Post-process the mermaid markdown file."""
    file_path = doc_path / "io_graph.md"
    if not file_path.exists():
        return
    with file_path.open("r") as file:
        file_content = file.read()
    # Remove the mermaid code block markers
    modified_content = file_content.replace("```mermaid", "")
    modified_content = modified_content.replace("```", "")
    with file_path.open("w") as file:
        file.write(modified_content)


def analyze_executable(
    pkg_name: str, exec_name: str, doc_path: Path, style_path: Path, max_duration: float
) -> None:
    """Run and introspect a a single ROS executable."""
    print("--- Analyzing executable:", pkg_name, exec_name, "---")
    launch_service = LaunchService()
    launch_service.include_launch_description(
        generate_launch_analysis_description(
            pkg_name, exec_name, doc_path, style_path, max_duration
        )
    )
    launch_service.run()
    launch_service.shutdown()
    post_process_mermaid_md(doc_path)


def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze all ROS executables in a folder."
    )
    parser.add_argument(
        "--src-path",
        type=str,
        default="/workspace/src",
        help="Path to the source folder containing ROS packages",
    )
    parser.add_argument(
        "--doc-path",
        type=str,
        default="/workspace/src/tmp",
        help="Path to the documentation folder",
    )
    parser.add_argument(
        "--graph-style",
        type=str,
        default="",
        help="Path to YAML graph style file",
    )
    parser.add_argument(
        "--max-duration",
        type=float,
        default=5.0,
        help="Maximum duration to run each executable for analysis [s]",
    )
    args = parser.parse_args()
    src_path = Path(args.src_path)
    doc_path = Path(args.doc_path)
    style_path = Path(args.graph_style)

    shutil.rmtree(doc_path, ignore_errors=True)
    create_directory(doc_path)
    for pkg_name in find_ros_packages(src_path):
        create_directory(doc_path / pkg_name)
        for exec_name in get_ros_executables(pkg_name):
            exec_doc_path = doc_path / pkg_name / exec_name.replace(".py", "_py")
            create_directory(exec_doc_path)
            analyze_executable(
                pkg_name, exec_name, exec_doc_path, style_path, args.max_duration
            )


if __name__ == "__main__":
    main()
