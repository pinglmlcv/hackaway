// using Box to allocate space on the heap
// box itself is allocated on the stack

#[derive(Debug)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

use List::{Cons, Nil};


fn main() {
    let list = Cons(1, 
        Box::new(Cons(2,
            Box::new(Cons(3,
                Box::new(Nil))))));
    println!("list contains: {:?}", list);
}