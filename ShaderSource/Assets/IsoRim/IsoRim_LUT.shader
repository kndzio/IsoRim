// IsoRim colour grading with a lookup table. Drawn by the mod as one sheet in front of the camera
// after everything else in the map view: it grabs what is already on screen, looks every pixel up
// in a 1024 x 32 LUT strip (32 slices of 32 x 32; blue picks the slice, red runs across, green up)
// and blends the result in by _Strength.
Shader "IsoRim/LUT"
{
    Properties
    {
        _LutTex ("LUT strip", 2D) = "white" {}
        _Strength ("Strength", Range(0, 1)) = 1
    }
    SubShader
    {
        Tags { "Queue" = "Overlay" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        ZWrite Off
        ZTest Always
        Cull Off

        GrabPass { "_IsoRimGrab" }

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _IsoRimGrab;
            sampler2D _LutTex;
            float _Strength;

            struct v2f
            {
                float4 pos : SV_POSITION;
                float4 grab : TEXCOORD0;
            };

            v2f vert(appdata_base v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);
                o.grab = ComputeGrabScreenPos(o.pos);
                return o;
            }

            float3 Lookup(float3 c)
            {
                const float size = 32.0;
                float slice = c.b * (size - 1.0);
                float s0 = floor(slice);
                float s1 = min(s0 + 1.0, size - 1.0);
                float f = slice - s0;
                float u = (c.r * (size - 1.0) + 0.5) / (size * size);
                float v = (c.g * (size - 1.0) + 0.5) / size;
                float3 a = tex2D(_LutTex, float2(u + s0 / size, v)).rgb;
                float3 b = tex2D(_LutTex, float2(u + s1 / size, v)).rgb;
                return lerp(a, b, f);
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float3 c = saturate(tex2Dproj(_IsoRimGrab, i.grab).rgb);
                return fixed4(lerp(c, Lookup(c), _Strength), 1.0);
            }
            ENDCG
        }
    }
}
