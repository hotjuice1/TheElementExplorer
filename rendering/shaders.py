"""OpenGL 3.3 sphere impostors: shared points with spherical lighting and depth."""
VERTEX = """#version 330 core
layout(location=0) in vec3 position;
layout(location=1) in vec3 color;
layout(location=2) in float radius;
uniform mat4 view;
uniform mat4 projection;
uniform float viewportHeight;
out vec3 tint;
out vec3 centerEye;
out float sphereRadius;
void main() {
    vec4 eye = view * vec4(position, 1.0);
    gl_Position = projection * eye;
    gl_PointSize = clamp(viewportHeight * projection[1][1] * radius / max(0.01, -eye.z), 1.0, 1024.0);
    tint = color;
    centerEye = eye.xyz;
    sphereRadius = radius;
}
"""
FRAGMENT = """#version 330 core
in vec3 tint;
in vec3 centerEye;
in float sphereRadius;
uniform mat4 projection;
uniform int style;
out vec4 fragColor;
void main() {
    if (style == 2) {
        fragColor = vec4(tint, 0.28);
        gl_FragDepth = gl_FragCoord.z;
        return;
    }
    vec2 uv = gl_PointCoord * 2.0 - 1.0;
    float rr = dot(uv, uv);
    if (rr > 1.0) discard;
    if (style == 1) {
        fragColor = vec4(tint, 0.30 * (1.0-rr));
        gl_FragDepth = gl_FragCoord.z;
        return;
    }
    vec3 normal = vec3(uv.x, -uv.y, sqrt(1.0-rr));
    float diffuse = max(0.0, dot(normal, normalize(vec3(-0.45,0.65,1.0))));
    float shine = pow(max(0.0, dot(normal, normalize(vec3(-0.3,0.4,1.0)))), 32.0);
    fragColor = vec4(tint * (0.32+0.68*diffuse) + vec3(0.42)*shine, 1.0);
    vec4 surface = projection * vec4(centerEye + normal*sphereRadius, 1.0);
    gl_FragDepth = (surface.z/surface.w)*0.5+0.5;
}
"""
