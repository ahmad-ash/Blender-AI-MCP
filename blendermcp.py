import bpy 
import socket
import threading
import json
import traceback
import time  # Added missing import
from bpy.props import IntProperty, BoolProperty

bl_info = {
    "name": "Ahmad's Claude MCP",
    "author": "Ahmad Ashfaq",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Minimal TCP server for Blender-AI communication",
    "category": "Interface",
}

class BlenderMCPServer:
    def __init__(self, port=9876):
        self.port = port
        self.running = False
        self.server_thread = None
        self.client_threads = []
        
    def start(self):
        if self.running:
            return
            
        self.running = True
        self.server_thread = threading.Thread(target=self._server_loop)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"MCP Server started on port {self.port}")
    
    def stop(self):
        self.running = False
        
        # Stop all client threads
        for thread in self.client_threads:
            if thread.is_alive():
                thread.join(timeout=0.5)
        
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
        
        print("MCP Server stopped")
    
    def _server_loop(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('localhost', self.port))
            sock.listen(5)
            sock.settimeout(1.0)
            
            while self.running:
                try:
                    client, addr = sock.accept()
                    print(f"Client connected: {addr}")
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    self.client_threads.append(client_thread)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Server error: {str(e)}")
    
    def _handle_client(self, client):
        with client:
            client.settimeout(5.0)  # Set timeout for client operations
            buffer = b''
            
            while self.running:
                try:
                    data = client.recv(4096)
                    if not data: 
                        break
                    
                    buffer += data
                    
                    # Try to parse JSON
                    try:
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''
                        
                        # Process command and send response
                        response = self.execute_command(command)
                        client.sendall(json.dumps(response).encode('utf-8'))
                    except json.JSONDecodeError:
                        # Incomplete JSON, wait for more data
                        continue
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Client error: {str(e)}")
                    traceback.print_exc()
                    break
        
        print("Client disconnected")
    
    def execute_command(self, command):
        try:
            handler = getattr(self, f"cmd_{command['type']}", None)
            if handler:
                return handler(command.get('params', {}))
            return {"status": "error", "message": f"Unknown command: {command['type']}"}
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    # Command handlers
    def cmd_get_scene_info(self, params):
        return {
            "status": "success",
            "scene": bpy.context.scene.name,
            "objects": [obj.name for obj in bpy.context.scene.objects]
        }
    
    def cmd_create_cube(self, params):
        size = params.get('size', 2.0)
        location = params.get('location', [0, 0, 0])
        
        def create():
            bpy.ops.mesh.primitive_cube_add(size=size, location=location)
            return {"name": bpy.context.object.name}
        
        return self._execute_in_main_thread(create)
    
    def cmd_create_sphere(self, params):
        radius = params.get('radius', 1.0)
        location = params.get('location', [0, 0, 0])
        
        def create():
            bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
            return {"name": bpy.context.object.name}
        
        return self._execute_in_main_thread(create)
    
    def cmd_create_cylinder(self, params):
        radius = params.get('radius', 1.0)
        depth = params.get('depth', 2.0)
        location = params.get('location', [0, 0, 0])
        
        def create():
            bpy.ops.mesh.primitive_cylinder_add(
                radius=radius, 
                depth=depth, 
                location=location
            )
            return {"name": bpy.context.object.name}
        
        return self._execute_in_main_thread(create)
    
    def cmd_execute_code(self, params):
        code = params.get('code', '')
        
        def execute():
            try:
                # Create a safe execution environment
                local_vars = {}
                exec(code, {"bpy": bpy, "math": __import__("math")}, local_vars)
                return {"result": "Code executed successfully"}
            except Exception as e:
                return {"error": str(e), "traceback": traceback.format_exc()}
        
        return self._execute_in_main_thread(execute)
    
    def cmd_clean_scene(self, params):
        def clean():
            # Unselect all
            bpy.ops.object.select_all(action='DESELECT')
            
            # Remove all objects
            for obj in bpy.context.scene.objects:
                obj.select_set(True)
            
            bpy.ops.object.delete()
            
            # Remove orphan data
            for block in bpy.data.meshes:
                if block.users == 0:
                    bpy.data.meshes.remove(block)
            
            for block in bpy.data.materials:
                if block.users == 0:
                    bpy.data.materials.remove(block)
            
            return {"result": "Scene cleaned"}
        
        return self._execute_in_main_thread(clean)
    
    # Utility function
    def _execute_in_main_thread(self, func):
        result = None
        event = threading.Event()
        
        def wrapper():
            nonlocal result
            try:
                result = func()
            except Exception as e:
                result = {"error": str(e), "traceback": traceback.format_exc()}
            finally:
                event.set()
            return None
        
        # Schedule in main thread
        bpy.app.timers.register(wrapper, first_interval=0.0)
        
        # Wait for completion with timeout
        event.wait(10.0)  # 10 second timeout
        
        if result is None:
            return {"status": "error", "message": "Operation timed out"}
        
        return {"status": "success", "result": result}

# UI Panel
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP Lite"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlenderMCP'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.prop(scene, "blendermcp_port")
        
        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Start Server")
        else:
            layout.operator("blendermcp.stop_server", text="Stop Server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")
            layout.operator("blendermcp.clean_scene", text="Clean Scene")

# Operators
class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Start MCP Server"
    
    def execute(self, context):
        if not hasattr(bpy.types, "mcp_server"):
            bpy.types.mcp_server = BlenderMCPServer(
                port=context.scene.blendermcp_port
            )
        bpy.types.mcp_server.start()
        context.scene.blendermcp_server_running = True
        return {'FINISHED'}

class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop MCP Server"
    
    def execute(self, context):
        if hasattr(bpy.types, "mcp_server"):
            bpy.types.mcp_server.stop()
            del bpy.types.mcp_server
        context.scene.blendermcp_server_running = False
        return {'FINISHED'}

class BLENDERMCP_OT_CleanScene(bpy.types.Operator):
    bl_idname = "blendermcp.clean_scene"
    bl_label = "Clean Scene"
    
    def execute(self, context):
        if hasattr(bpy.types, "mcp_server"):
            response = bpy.types.mcp_server.execute_command({
                "type": "clean_scene"
            })
            if response.get("status") == "success":
                self.report({'INFO'}, "Scene cleaned")
            else:
                self.report({'ERROR'}, "Failed to clean scene")
        return {'FINISHED'}

# Registration
def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        default=9876,
        min=1024,
        max=65535
    )
    bpy.types.Scene.blendermcp_server_running = BoolProperty(default=False)
    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    bpy.utils.register_class(BLENDERMCP_OT_CleanScene)

def unregister():
    if hasattr(bpy.types, "mcp_server"):
        bpy.types.mcp_server.stop()
        del bpy.types.mcp_server
        
    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_CleanScene)
    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running

if __name__ == "__main__":
    register()
