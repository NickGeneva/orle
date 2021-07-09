// Gmsh project created on Fri Jul  9 10:06:25 2021
// Name: Flow around a cylinder
// Author: Nicholas Geneva
// 
// Export to .msh version 2 ascii
// Then use: gmshToFoam cylinder_rot_mesh.msh -case ./cylinder
// Set up cyclic boundaries in the polymesh/boundaries

SetFactory("OpenCASCADE");

// Cylinder wall
Point(1) = {0, -0, 0, 1.0};
//+
Point(2) = {-0.05, 0, 0, 1.0};
//+
Point(3) = {0.05, 0, 0, 1.0};
//+
Point(4) = {0, 0.05, 0, 1.0};
//+
Point(5) = {0, -0.05, 0, 1.0};
//+
Circle(1) = {3, 1, 4};
//+
Circle(2) = {4, 1, 2};
//+
Circle(3) = {2, 1, 5};
//+
Circle(4) = {5, 1, 3};

// Outer circle
Point(6) = {-0.1, 0, 0, 1.0};
//+
Point(7) = {0.1, 0, 0, 1.0};
//+
Point(8) = {0, 0.1, 0, 1.0};
//+
Point(9) = {0, -0.1, 0, 1.0};
//+
Circle(5) = {7, 1, 8};
//+
Circle(6) = {8, 1, 6};
//+
Circle(7) = {6, 1, 9};
//+
Circle(8) = {9, 1, 7};

// Connecting Lines
Line(9) = {3, 7};
//+
Line(10) = {4, 8};
//+
Line(11) = {2, 6};
//+
Line(12) = {5, 9};

// Near cylinder region
Point(10) = {0.15, 0.15, -0, 1.0};
//+
Point(11) = {-0.15, 0.15, -0, 1.0};
//+
Point(12) = {-0.15, -0.15, -0, 1.0};
//+
Point(13) = {0.15, -0.15, -0, 1.0};
//+
Line(13) = {10, 11};
//+
Line(14) = {11, 12};
//+
Line(15) = {12, 13};
//+
Line(16) = {13, 10};

// Outer box
Point(14) = {2, 0.21, -0, 1.0};
//+
Point(15) = {-0.2, 0.21, -0, 1.0};
//+
Point(16) = {-0.2, -0.2, -0, 1.0};
//+
Point(17) = {2, -0.2, -0, 1.0};
//+
Line(17) = {14, 15};
//+
Line(18) = {15, 16};
//+
Line(19) = {16, 17};
//+
Line(20) = {17, 14};
//+

// Mesh cylinder
// Cylinder wall resolution
Transfinite Curve {3, 2, 1, 4, 8, 5, 6, 7} = 40 Using Progression 1;
// wall normal resolution
Transfinite Curve {11, 10, 9, 12} = 30 Using Progression 1.05;
//+
Curve Loop(1) = {1, 10, -5, -9};
//+
Plane Surface(1) = {1};
//+
Curve Loop(2) = {10, 6, -11, -2};
//+
Plane Surface(2) = {2};
//+
Curve Loop(3) = {3, 12, -7, -11};
//+
Plane Surface(3) = {3};
//+
Curve Loop(4) = {4, 9, -8, -12};
//+
Plane Surface(4) = {4};
//+
Transfinite Surface {3};
//+
Transfinite Surface {1};
//+
Transfinite Surface {2};
//+
Transfinite Surface {4};
//+
Recombine Surface {3, 2, 1, 4};


// Near cylinder box mesh
Transfinite Curve {14, 13, 16, 15} = 50 Using Progression 1;
//+
Curve Loop(5) = {14, 15, 16, 13};
//+
Curve Loop(6) = {7, 8, 5, 6};
//+
Plane Surface(5) = {5, 6};

// Outer region mesh
// Inlet/outlet resolution
Transfinite Curve {18, 20} = 50 Using Progression 1;
// Channel walls resolution
Transfinite Curve {17, 19} = 300 Using Progression 1;
//+
Curve Loop(7) = {18, 19, 20, 17};
//+
Curve Loop(8) = {13, 14, 15, 16};
//+
Plane Surface(6) = {7, 8};


// Extrude into 3D
Extrude {0, 0, 0.01} {
  Surface{6}; Surface{5}; Surface{1}; Surface{4}; Surface{3}; Surface{2}; 
  Layers {1}; 
  Recombine;
}


//+
Physical Surface("cylinder", 57) = {28, 31, 21, 25};
//+
Physical Surface("wall", 58) = {10, 8};
//+
Physical Surface("outlet", 59) = {9};
//+
Physical Surface("inlet", 60) = {7};
//+
Physical Surface("cyclic1", 61) = {15, 20, 27, 24, 32, 30};
//+
Physical Surface("cyclic2", 62) = {6, 1, 5, 2, 3, 4};
//+
Physical Volume("Volume", 63) = {3, 4, 5, 6, 2, 1};
