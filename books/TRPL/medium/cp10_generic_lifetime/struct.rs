// generic struct

struct Point<T, U> {
    x: T,
    y: U,
}

// this example show that generic type can be different in 
// struct definition and method
impl<T, U> Point<T, U> {
    fn mixup<V, W>(self, other: Point<V, W>) -> Point<T, W> {
        Point {
            x: self.x,
            y: other.y,
        }
    }
}

fn main() {
    let p1 = Point {x: 5, y: 10.4};
    let p2 = Point {x: "hello", y: 'c'};

    let p3 = p1.mixup(p2);

    println!("p3.x = {}, p3.y = {}", p3.x, p3.y);
    // println!("p1.x = {}, p1.y = {}", p1.x, p1.y); 
    // println!("p2.x = {}, p2.y = {}", p2.x, p2.y); // move
}