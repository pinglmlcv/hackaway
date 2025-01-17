pub fn remove_duplicates(nums: &mut Vec<i32>) -> i32 {
    let len = nums.len();
    if nums.len() == 0 { return 0; }

    let mut k = 0; // 下标为0的数直接入选 
    for i in 1..len {
        let v = nums[i];
        if v != nums[k] {
            k += 1;
            nums[k] = v;
        }
    }
    (k + 1) as i32
}

pub fn remove_element(nums: &mut Vec<i32>, val: i32) -> i32 {
    let len = nums.len();
    if len == 0 { return 0; }

    let mut k = 0; // 指向可以插入的位置
    for i in 0..len {
        if nums[i] != val {
            nums[k] = nums[i];
            k += 1;
        }
    }
    k as i32 
}